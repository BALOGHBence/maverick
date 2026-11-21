"""
Engine side of process isolation.

:class:`ProcessPlayer` runs a player in its own worker process and forwards
``decide_action`` and the player's event hooks to it. Workers are started with the
``spawn`` method, so they share no memory with the engine. With ``fork``, a worker
would inherit a copy of the engine, including the state of the random number generator
that shuffles the deck.

Security boundary: replies from workers are untrusted, so they are read as raw bytes of
limited size and decoded as JSON. Never unpickle anything a worker sends, and don't
replace the pipe with a ``multiprocessing.Queue``, which unpickles what it receives.
"""

import hashlib
import json
import logging
import multiprocessing
import pickle  # nosec B403 - only used to send the player to its worker
import time
import weakref
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any, Callable, Optional

from pydantic import ValidationError

from ..enums import GameEventType
from ..events import GameEvent
from ..player import Player
from ..playeraction import PlayerAction
from ..playerview import PlayerView
from .worker import ViewDelta, run_worker

__all__ = ["PlayerFailure", "ProcessPlayer", "derive_player_seed"]

# Upper limit for the size of a reply from a worker, so a misbehaving worker can't make
# the engine allocate arbitrary amounts of memory.
MAX_REPLY_BYTES = 1_000_000
# Seconds to wait for a worker to start up and to shut down
START_TIMEOUT = 60.0
CLOSE_TIMEOUT = 5.0


class PlayerFailure(Exception):
    """An isolated player failed to produce an action.

    Raised when the worker times out, raises an exception, returns something that is
    not a valid ``PlayerAction``, or has died. The engine folds the player's hand.

    .. versionadded:: 0.7.0
    """


def derive_player_seed(game_seed: int, player_uid: str, hand_number: int) -> int:
    """Seed for the random number generators of an isolated player.

    The seed depends on the game's seed, the player and the hand, so players get
    different random numbers, and so do the hands of a game. It doesn't depend on the
    state of the game's own generator, so it can't be used to predict the cards. The
    derivation uses SHA-256 rather than :func:`hash`, which differs between
    interpreters.

    Parameters
    ----------
    game_seed : int
        The seed of the game.
    player_uid : str
        The UID of the player.
    hand_number : int
        The number of the hand, ``0`` before the first hand.

    Returns
    -------
    int
        A non-negative integer below ``2**64``.
    """
    data = f"maverick-player-seed:{game_seed}:{player_uid}:{hand_number}".encode()
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big")


def _overridden_hooks(player: Any) -> list[str]:
    """Names of the event hooks ``player`` implements, as ``Game._emit`` sees them."""
    hooks = []
    fn = getattr(player, "on_event", None)
    if callable(fn) and getattr(fn, "__func__", None) is not Player.on_event:
        hooks.append("on_event")
    for event_type in GameEventType:
        name = f"on_{event_type.name.lower()}"
        if callable(getattr(player, name, None)):
            hooks.append(name)
    return hooks


def _shutdown(process: BaseProcess, conn: Connection) -> None:
    if process.is_alive():
        process.terminate()
        process.join(1.0)
    conn.close()


class ProcessPlayer:
    """Runs a player in a worker process and forwards calls to it.

    The proxy satisfies :class:`~maverick.protocol.PlayerLike`. It exposes the same
    event hooks as the wrapped player, so the engine calls only the hooks the player
    implements.

    Parameters
    ----------
    player : PlayerLike
        The player to run in a worker process. It must be picklable, and its class
        must be importable in a fresh interpreter.
    decision_timeout : float | None
        Maximum number of seconds to wait for a decision. ``None`` means no limit.
    logger : logging.Logger
        Logger for problems reported by the worker.
    seed : int | None
        Seed for the random number generators of the worker, set before the player is
        unpickled. If None, the worker's generators are seeded from the operating
        system, as in any new interpreter.

    .. versionadded:: 0.7.0
    """

    def __init__(
        self,
        player: Any,
        *,
        decision_timeout: Optional[float],
        logger: logging.Logger,
        seed: Optional[int] = None,
    ) -> None:
        self.player = player
        self.uid: Optional[str] = player.uid
        self.name: Optional[str] = player.name
        self._timeout = decision_timeout
        self._seed = seed
        self._logger = logger
        self._seq = 0
        self._sent_events = 0
        self._rules_sent = False
        self._dead = False
        self._process: Optional[BaseProcess] = None
        self._conn: Optional[Connection] = None
        self._finalizer: Optional[weakref.finalize] = None
        self._final_state: Optional[dict[str, Any]] = None
        for name in _overridden_hooks(player):
            setattr(self, name, self._make_hook(name))

    @property
    def process(self) -> Optional[BaseProcess]:
        """The worker process, or ``None`` before :meth:`start`."""
        return self._process

    @property
    def is_alive(self) -> bool:
        """Whether the worker is running and able to take decisions."""
        return not self._dead and self._process is not None and self._process.is_alive()

    @property
    def final_state(self) -> Optional[dict[str, Any]]:
        """The state the player exported when its worker was closed, if any."""
        return self._final_state

    def start(self) -> None:
        """Start the worker process and wait until it has loaded the player.

        Raises
        ------
        TypeError
            If the player can't be pickled.
        RuntimeError
            If the worker can't load the player or doesn't start in time.
        """
        try:
            # Pickles the caller's own player for the worker. Replies from the
            # worker are never unpickled.
            payload = pickle.dumps(self.player)  # nosemgrep
        except Exception as exc:
            raise TypeError(
                f"Player {self.name!r} can't be run in a worker process because it "
                f"can't be pickled: {exc}"
            ) from exc

        seed = self._seed
        ctx = multiprocessing.get_context("spawn")
        conn, child_conn = ctx.Pipe(duplex=True)
        process = ctx.Process(
            target=run_worker,
            args=(child_conn, payload, seed),
            name=f"maverick-player-{self.name}",
            daemon=True,
        )
        process.start()
        child_conn.close()
        self._process, self._conn = process, conn
        self._finalizer = weakref.finalize(self, _shutdown, process, conn)

        reply = None
        try:
            if conn.poll(START_TIMEOUT):
                reply = self._parse(conn.recv_bytes(MAX_REPLY_BYTES))
        except (EOFError, OSError, PlayerFailure):
            pass
        if not reply or reply.get("ready") is not True:
            self._dead = True
            self._finalizer()
            error = reply.get("error") if reply else "no response"
            raise RuntimeError(
                f"The worker process of player {self.name!r} failed to load the "
                f"player. Its class must be importable in a fresh interpreter, so it "
                f"can't be defined in a notebook or an interactive session.\n{error}"
            )

    def close(self) -> None:
        """Ask the worker to exit, and terminate it if it doesn't.

        The worker exports the state of the player before it exits, which is
        available as :attr:`final_state` afterwards.
        """
        if self._process is None or self._finalizer is None:
            return
        if not self._dead:
            deadline = time.monotonic() + CLOSE_TIMEOUT
            try:
                self._conn.send(("close",))
                while self._conn.poll(max(0.0, deadline - time.monotonic())):
                    reply = self._parse(self._conn.recv_bytes(MAX_REPLY_BYTES))
                    self._log_hook_errors(reply)
                    if reply.get("closed") is True:
                        self._final_state = self._state_from_reply(reply)
                        break
            except (EOFError, OSError, PlayerFailure) as exc:
                self._logger.warning(
                    f"Could not get the final state of player {self.name}: {exc}"
                )
            self._process.join(max(0.0, deadline - time.monotonic()))
            self._dead = True
        self._finalizer()

    def reseed(self, seed: int) -> None:
        """Seed the random number generators of the worker.

        The worker handles messages in order, so everything the player does after
        this call uses the new seed. Does nothing if the worker is not running.
        """
        self._seed = seed
        if not self._dead and self._conn is not None:
            self._send(("seed", seed), fail=False)

    def decide_action(self, *, game: PlayerView, **kwargs: Any) -> PlayerAction:
        """Forward a decision to the worker and return its action.

        Raises
        ------
        PlayerFailure
            If no valid action is received.
        """
        reply = self._request(
            lambda seq: ("decide", seq, self._delta(game), kwargs), "decide"
        )
        if reply.get("error"):
            raise PlayerFailure(
                f"decide_action of player {self.name!r} raised an exception:\n"
                f"{reply['error']}"
            )
        try:
            return PlayerAction.model_validate(reply.get("action"))
        except ValidationError as exc:
            raise PlayerFailure(
                f"Player {self.name!r} returned an invalid action: {exc}"
            ) from exc

    def export_state(self) -> Optional[dict[str, Any]]:
        """Ask the worker for the state the player exports.

        Returns
        -------
        dict | None
            What the player's ``export_state`` returned, or ``None`` if the player
            doesn't implement it.

        Raises
        ------
        PlayerFailure
            If the worker doesn't answer in time, has died, or ``export_state``
            raised an exception or returned something that is not JSON-serializable.
        """
        reply = self._request(lambda seq: ("export", seq), "export its state")
        return self._state_from_reply(reply)

    def import_state(self, state: dict[str, Any]) -> None:
        """Ask the worker to restore ``state`` with the player's ``import_state``.

        Raises
        ------
        PlayerFailure
            If the worker doesn't answer in time, has died, or ``import_state``
            raised an exception.
        """
        reply = self._request(lambda seq: ("import", seq, state), "import its state")
        if reply.get("state_error"):
            raise PlayerFailure(
                f"import_state of player {self.name!r} failed:\n"
                f"{reply['state_error']}"
            )

    def _request(
        self, build_message: Callable[[int], tuple], what: str
    ) -> dict[str, Any]:
        """Send a request to the worker and wait for the reply with the same seq."""
        if self._dead or self._conn is None:
            raise PlayerFailure(f"The worker of player {self.name!r} is not running")
        self._seq += 1
        seq = self._seq
        self._send(build_message(seq), fail=True)

        deadline = None if self._timeout is None else time.monotonic() + self._timeout
        while True:
            remaining = None if deadline is None else deadline - time.monotonic()
            try:
                ready = self._conn.poll(
                    None if remaining is None else max(0, remaining)
                )
                raw = self._conn.recv_bytes(MAX_REPLY_BYTES) if ready else None
            except (EOFError, OSError) as exc:
                self._mark_dead()
                raise PlayerFailure(
                    f"The worker of player {self.name!r} died or sent an invalid reply"
                ) from exc
            if raw is None:
                raise PlayerFailure(
                    f"Player {self.name!r} did not {what} within {self._timeout}s"
                )
            reply = self._parse(raw)
            self._log_hook_errors(reply)
            if reply.get("seq") == seq:
                return reply
            # otherwise it's a late reply to a request that timed out

    def _state_from_reply(self, reply: dict[str, Any]) -> Optional[dict[str, Any]]:
        if reply.get("state_error"):
            raise PlayerFailure(
                f"export_state of player {self.name!r} failed:\n"
                f"{reply['state_error']}"
            )
        state = reply.get("state")
        if state is not None and not isinstance(state, dict):
            raise PlayerFailure(
                f"The worker of player {self.name!r} sent a malformed state"
            )
        return state

    def _make_hook(self, name: str) -> Callable[[GameEvent, PlayerView], None]:
        def hook(event: GameEvent, game: PlayerView) -> None:
            if not self._dead and self._conn is not None:
                self._send(("hook", name, event, self._delta(game)), fail=False)

        hook.__name__ = name
        return hook

    def _delta(self, view: PlayerView) -> ViewDelta:
        new_events = list(view.history[self._sent_events :])
        self._sent_events = len(view.history)
        rules = None
        if not self._rules_sent:
            rules, self._rules_sent = view.rules, True
        return ViewDelta(
            player_uid=view.player_uid,
            game_uid=view.game_uid,
            state=view.state,
            new_events=new_events,
            rules=rules,
        )

    def _send(self, message: tuple, *, fail: bool) -> None:
        try:
            self._conn.send(message)
        except (EOFError, OSError) as exc:
            self._mark_dead()
            if fail:
                raise PlayerFailure(
                    f"The worker of player {self.name!r} is not running"
                ) from exc

    def _mark_dead(self) -> None:
        if not self._dead:
            self._dead = True
            self._logger.warning(
                f"The worker process of player {self.name} stopped, "
                f"the player folds from now on."
            )
            if self._finalizer is not None:
                self._finalizer()

    def _parse(self, raw: bytes) -> dict[str, Any]:
        try:
            reply = json.loads(raw)
        except ValueError as exc:
            raise PlayerFailure(
                f"The worker of player {self.name!r} sent a reply that is not JSON"
            ) from exc
        if not isinstance(reply, dict):
            raise PlayerFailure(
                f"The worker of player {self.name!r} sent a malformed reply"
            )
        return reply

    def _log_hook_errors(self, reply: dict[str, Any]) -> None:
        errors = reply.get("hook_errors")
        if not isinstance(errors, list):
            return
        for error in errors:
            if not isinstance(error, dict):
                continue
            self._logger.warning(
                f"Exception in player {self.name} {error.get('hook')} hook for "
                f"{error.get('event')}:\n{error.get('traceback')}"
            )
