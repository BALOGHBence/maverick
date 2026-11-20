"""
Bot side of process isolation.

:func:`run_worker` runs in a child process. It receives pickled messages from the
trusted engine and answers with JSON only, so the engine never unpickles anything that
comes from the worker.

Messages from the engine:

- ``("hook", name, event, delta)``: call the hook ``name``. There is no reply.
- ``("decide", seq, delta, kwargs)``: call ``decide_action`` and reply with
  ``{"seq", "action", "error", "hook_errors"}``.
- ``("export", seq)``: call ``export_state`` and reply with
  ``{"seq", "state", "state_error", "hook_errors"}``.
- ``("import", seq, state)``: call ``import_state`` and reply with
  ``{"seq", "state_error", "hook_errors"}``.
- ``("close",)``: export the state one last time, reply with
  ``{"closed": true, "state", "state_error", "hook_errors"}`` and exit.

``delta`` is a :class:`ViewDelta`, from which the worker rebuilds the
:class:`~maverick.playerview.PlayerView` of its player.
"""

import json
import pickle  # nosec B403 - only loads the player sent by the engine
import traceback
from multiprocessing.connection import Connection
from typing import Any, NamedTuple, Optional

from ..events import GameEvent
from ..player import Player
from ..playeraction import PlayerAction
from ..playerview import EventHistoryView, PlayerView
from ..rules import PokerRules
from ..state import GameState

__all__ = ["ViewDelta", "run_worker"]


class ViewDelta(NamedTuple):
    """What a worker needs to rebuild the current view of its player."""

    player_uid: str
    game_uid: Optional[str]
    state: GameState
    new_events: list[GameEvent]
    rules: Optional[PokerRules]  # only sent with the first message


class _Worker:
    def __init__(self, player: Any) -> None:
        self.player = player
        self.history: list[GameEvent] = []
        self.rules: Optional[PokerRules] = None
        self.hook_errors: list[dict[str, str]] = []

    def view(self, delta: ViewDelta) -> PlayerView:
        if delta.rules is not None:
            self.rules = delta.rules
        self.history.extend(delta.new_events)
        view = PlayerView(
            player_uid=delta.player_uid,
            game_uid=delta.game_uid,
            state=delta.state,
            rules=self.rules,
            history=EventHistoryView(self.history),
        )
        if isinstance(self.player, Player):
            self.player._view = view
        return view

    def take_hook_errors(self) -> list[dict[str, str]]:
        errors, self.hook_errors = self.hook_errors, []
        return errors

    def call_hook(self, name: str, event: GameEvent, delta: ViewDelta) -> None:
        view = self.view(delta)
        try:
            getattr(self.player, name)(event, view)
        except Exception:
            self.hook_errors.append(
                {
                    "hook": name,
                    "event": event.type.name,
                    "traceback": traceback.format_exc(),
                }
            )

    def decide(self, seq: int, delta: ViewDelta, kwargs: dict[str, Any]) -> bytes:
        view = self.view(delta)
        reply: dict[str, Any] = {"seq": seq, "action": None, "error": None}
        try:
            action = self.player.decide_action(game=view, **kwargs)
            if not isinstance(action, PlayerAction):
                raise TypeError(
                    "decide_action must return a PlayerAction, "
                    f"got {type(action).__name__}"
                )
            reply["action"] = action.model_dump(mode="json")
        except Exception:
            reply["error"] = traceback.format_exc()
        reply["hook_errors"] = self.take_hook_errors()
        return json.dumps(reply).encode()

    def export(self, **reply: Any) -> bytes:
        """Reply with the state the player exports, plus any extra ``reply`` fields."""
        reply.update(state=None, state_error=None)
        try:
            export_state = getattr(self.player, "export_state", None)
            state = export_state() if callable(export_state) else None
            if state is not None and not isinstance(state, dict):
                raise TypeError(
                    "export_state must return a dict or None, "
                    f"got {type(state).__name__}"
                )
            json.dumps(state)  # fail here, not when the reply is built
            reply["state"] = state
        except Exception:
            reply["state_error"] = traceback.format_exc()
        reply["hook_errors"] = self.take_hook_errors()
        return json.dumps(reply).encode()

    def import_(self, seq: int, state: dict[str, Any]) -> bytes:
        """Restore a state with the player's ``import_state`` and reply."""
        reply: dict[str, Any] = {"seq": seq, "state_error": None}
        try:
            import_state = getattr(self.player, "import_state", None)
            if not callable(import_state):
                raise TypeError("the player doesn't implement import_state")
            import_state(state)
        except Exception:
            reply["state_error"] = traceback.format_exc()
        reply["hook_errors"] = self.take_hook_errors()
        return json.dumps(reply).encode()


def run_worker(conn: Connection, player_bytes: bytes) -> None:
    """Serve one player in a worker process until the engine closes the connection.

    Parameters
    ----------
    conn : Connection
        The worker's end of the pipe to the engine.
    player_bytes : bytes
        The pickled player object.
    """
    try:
        # The bytes come from the engine that started this worker, not from a bot.
        player = pickle.loads(player_bytes)  # nosec B301  # nosemgrep
        worker = _Worker(player)
    except Exception:
        conn.send_bytes(
            json.dumps({"ready": False, "error": traceback.format_exc()}).encode()
        )
        return
    del player_bytes
    conn.send_bytes(json.dumps({"ready": True}).encode())

    while True:
        try:
            message = conn.recv()
        except (EOFError, OSError):
            return  # the engine went away
        kind = message[0]
        if kind == "hook":
            worker.call_hook(*message[1:])
        elif kind == "decide":
            conn.send_bytes(worker.decide(*message[1:]))
        elif kind == "export":
            conn.send_bytes(worker.export(seq=message[1]))
        elif kind == "import":
            conn.send_bytes(worker.import_(*message[1:]))
        elif kind == "close":
            conn.send_bytes(worker.export(closed=True))
            return
