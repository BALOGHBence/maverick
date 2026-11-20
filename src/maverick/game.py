"""
Poker Game State Machine.

This module implements a complete poker game using a state machine
architecture. The game manages player actions, betting rounds, card dealing, and
pot distribution.
"""

from __future__ import annotations

from typing import Deque, Iterable, Optional
from collections import deque
import json
import logging
import os
from pathlib import Path
import random
import time
import uuid
from warnings import warn
import warnings

from ._isolation import PlayerFailure, ProcessPlayer
from .config import IsolationSettings, resolve_settings
from .deck import Deck
from .enums import (
    ActionType,
    GameEventType,
    GameStage,
    PlayerIsolation,
    PlayerStateType,
    Street,
    Suit,
)
from .events import GameEvent
from .holding import Holding
from .protocol import PlayerLike, EventHandler
from .state import GameState
from .player import Player
from .playeraction import PlayerAction
from .playerstate import PlayerState, PlayerSnapshot
from .playerview import EventHistoryView, PlayerView, redact_event, redact_state
from .utils import find_highest_scoring_hand
from .eventbus import EventBus
from .rules import PokerRules, DealingRules, StakesRules, ShowdownRules
from .savegame import (
    SAVE_FORMAT_VERSION,
    Checkpoint,
    PlayerRecord,
    SaveFormatError,
    SaveWriter,
    SeatRecord,
    TableRecord,
    directory_has_save,
    new_header,
    parse_event,
    read_checkpoint,
    read_event_lines,
    read_header,
    truncate_event_log,
)
from .table import Table

__all__ = ["Game"]


class Game:
    """
    Texas Hold'em Poker Game.

    Implements a Texas Hold'em poker game using an event-driven state machine.
    The game manages player actions, betting rounds, dealing, and pot distribution.

    Parameters
    ----------
    small_blind : int
        Amount for the small blind.
    big_blind : int
        Amount for the big blind.
    ante : int
        Amount for the ante.
    min_players : int
        Minimum number of players to start the game.
    max_players : int
        Maximum number of players allowed at the table.
    max_hands : int
        Maximum number of hands to play before ending the game. Default is 1000.
    exc_handling_mode : {"log", "raise"}
        If "raise", exceptions in event handlers will propagate. If "log", they will be logged. This setting
        only effects event handling, not game logic. If an exception occurs in game logic, it will always raise.
    log_events : bool
        If True, game events will be logged to the console. This only affects logging, not event handling.
        The purpose of this is allow users to have their own event handlers without excessive logging noise.
    rules : PokerRules | None
        Custom poker rules to use. If None, default Texas Hold'em rules are applied. When provided, other
        parameters (small_blind, big_blind, ante, min_players, max_players) will override the corresponding
        fields in the rules.
    first_button_position : int | None
        The seat index of the player who will be the button in the first hand. If None (the default), the
        button is assigned randomly using a card draw.
    player_isolation : PlayerIsolation | str | None
        Where the code of the players runs. ``"none"`` runs players in the engine's process, ``"process"``
        runs every player in its own worker process. If None (the default), the value is taken from the
        ``MAVERICK_PLAYER_ISOLATION`` environment variable, then from ``[tool.maverick]`` in
        ``pyproject.toml``, and falls back to ``"none"``.

        .. versionadded:: 0.7.0
    decision_timeout : float | None
        Maximum number of seconds an isolated player may take to decide. A player that exceeds it folds.
        Resolved like ``player_isolation`` (environment variable ``MAVERICK_DECISION_TIMEOUT``). Only applies
        to isolated players. If not set anywhere, there is no limit.

        .. versionadded:: 0.7.0
    seed : int | None
        Seed of the game's own random number generator, which shuffles the deck and draws the first button.
        Games with the same seed, players and decisions deal the same cards. If None (the default), a seed
        is drawn from the global ``random`` module, so seeding ``random`` before creating the game keeps
        working. The generator is never shared with players, so players that use random numbers don't
        change the cards that are dealt.

        .. versionadded:: 0.7.0
    save_dir : str | os.PathLike | None
        Directory to save the game to, for replay with :class:`~maverick.replay.Replay`
        and to resume it with :meth:`load`. The game writes the events of every hand,
        and a checkpoint to resume from, each time a hand ends. The directory is
        created when the game starts. It must not hold a saved game already. If None
        (the default), the game is not saved.

        .. versionadded:: 0.7.0

    Notes
    -----
    With process isolation, worker processes are started when players are added and stopped when they
    leave, are eliminated or the game ends. Use the game as a context manager, or call :meth:`close`, to
    stop them early. Scripts that use process isolation must guard their entry point with
    ``if __name__ == "__main__":``.
    """

    def __init__(
        self,
        *,
        small_blind: Optional[int] = None,
        big_blind: Optional[int] = None,
        ante: Optional[int] = None,
        min_players: Optional[int] = 2,
        max_players: Optional[int] = None,
        max_hands: int = 1000,
        exc_handling_mode: str = "log",
        log_events: bool = True,
        rules: Optional[PokerRules] = None,
        first_button_position: Optional[int] = None,
        player_isolation: Optional[PlayerIsolation | str] = None,
        decision_timeout: Optional[float] = None,
        seed: Optional[int] = None,
        save_dir: Optional[str | os.PathLike] = None,
    ):
        if not exc_handling_mode in ["log", "raise"]:
            raise ValueError("exc_handling_mode must be 'log' or 'raise'")

        if rules is None:
            rules = PokerRules(
                dealing=DealingRules(),
                stakes=StakesRules(
                    small_blind=small_blind,
                    big_blind=big_blind,
                ),
                showdown=ShowdownRules(),
            )

        if small_blind:
            rules.stakes.small_blind = small_blind

        if big_blind:
            rules.stakes.big_blind = big_blind

        if ante:
            rules.stakes.ante = ante

        if min_players:
            rules.dealing.min_players = min_players

        if max_players:
            rules.dealing.max_players = max_players

        if first_button_position is not None:
            if not isinstance(first_button_position, int):
                raise ValueError("first_button_position must be an integer")

            if not first_button_position >= 0:
                raise ValueError("first_button_position must be non-negative")

        self._settings = resolve_settings(
            player_isolation=player_isolation, decision_timeout=decision_timeout
        )

        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise ValueError("seed must be an integer")

        # The game's own random number generator, so players that use the global
        # ``random`` module can neither change nor predict the cards that are dealt.
        # It must be seedable for reproducible games, so ``secrets`` can't be used.
        self._seed = seed if seed is not None else random.getrandbits(64)  # nosec B311
        self._rng = random.Random(self._seed)  # nosec B311

        self._rules = rules
        self._max_hands = max_hands
        self._state = GameState(
            small_blind=rules.stakes.small_blind,
            big_blind=rules.stakes.big_blind,
            ante=rules.stakes.ante,
        )
        self._event_queue: Deque[GameEventType] = deque()
        self._logger = logging.getLogger("maverick")
        self._log_events = log_events
        self._first_button_position = first_button_position
        self._all_stacks_at_game_start = 0

        # Event handling
        self._events = EventBus(strict=exc_handling_mode == "raise")
        self._event_history: list[GameEvent] = []
        # Per-player copies of ``_event_history`` (without GAME_STATE_CHANGED events),
        # synced on demand, and the number of events already synced for each player.
        self._player_histories: dict[str, list[GameEvent]] = {}
        self._player_history_synced: dict[str, int] = {}
        # Per-player copies of the rules, handed out in player views
        self._player_rules: dict[str, PokerRules] = {}
        # UIDs of players who revealed their holding at showdown in the current hand
        self._revealed_uids: set[str] = set()

        # Table
        self._table = Table(n_seats=rules.dealing.max_players)

        # Game UID - assigned when GAME_STARTED is processed
        self._game_uid: Optional[str] = None

        # Strategy objects - keyed by player UID; separate from GameState snapshots
        self._strategies: dict[str, PlayerLike] = {}
        # Proxies of players running in worker processes, keyed by player UID. The
        # engine calls these instead of the strategy objects.
        self._proxies: dict[str, ProcessPlayer] = {}
        # States exported by isolated players when their workers were stopped
        self._final_states: dict[str, Optional[dict]] = {}

        # Active deck - held here, not in GameState
        self._deck: Optional[Deck] = None

        # Saving to disk
        self._save: Optional[SaveWriter] = None
        if save_dir is not None:
            directory = Path(save_dir)
            if directory_has_save(directory):
                raise FileExistsError(
                    f"{directory} already holds a saved game. Use Game.load to "
                    f"continue it, or choose another directory."
                )
            self._save = SaveWriter(directory)
        # Set by load(): start() continues the loaded game instead of a new one
        self._resuming = False

    @property
    def game_uid(self) -> Optional[str]:
        """Returns the unique identifier for the current game session.

        A new ``game_uid`` is generated each time :meth:`start` is called (i.e.
        each time the ``GAME_STARTED`` event is processed). The value is
        ``None`` before the game has been started.

        Returns
        -------
        str | None
            A 32-character hexadecimal UUID string, or ``None`` if the game
            has not been started yet.

        .. versionadded:: 0.5.0
        """
        return self._game_uid

    @property
    def uid(self) -> Optional[str]:
        """Alias for game_uid."""
        return self._game_uid

    @property
    def game_id(self) -> Optional[str]:
        """Deprecated: use ``uid`` instead."""
        warnings.warn(
            "Game.game_id is deprecated, use Game.uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._game_uid

    @property
    def rules(self) -> PokerRules:
        """Returns the poker rules used in this game."""
        return self._rules

    @property
    def state(self) -> GameState:
        """Returns the current game state."""
        return self._state

    @property
    def deck(self) -> Optional[Deck]:
        """The current deck. Exposes live engine state — not a historical snapshot."""
        return self._deck

    @property
    def history(self) -> list[GameEvent]:
        """Returns the event history.

        Returns
        -------
        list[GameEvent]
            A list of all game events in chronological order.
        """
        return self._event_history

    @property
    def seed(self) -> int:
        """The seed of the game's random number generator.

        Passing it to a new game, with the same players and decisions, deals the same
        cards. It is not part of :attr:`state`, so players never see it.

        .. versionadded:: 0.7.0
        """
        return self._seed

    @property
    def save_dir(self) -> Optional[Path]:
        """The directory the game is saved to, or None if it is not saved.

        .. versionadded:: 0.7.0
        """
        return self._save.directory if self._save is not None else None

    @property
    def settings(self) -> IsolationSettings:
        """The resolved isolation settings of the game.

        .. versionadded:: 0.7.0
        """
        return self._settings

    @property
    def table(self) -> Table:
        """Returns the game table.

        .. versionadded:: 0.2.0
        """
        return self._table

    @property
    def button(self) -> Optional[PlayerLike]:
        """Returns the player currently on the button, or None if no button assigned.

        .. versionadded:: 0.3.0
        """
        if self.state.button_position is not None:
            uid = self.table[self.state.button_position]
            return self._strategies.get(uid) if uid else None
        return None

    @property
    def small_blind(self) -> Optional[PlayerLike]:
        """Returns the player currently in the small blind position, or None if no small blind assigned.

        .. versionadded:: 0.3.0
        """
        if self.state.small_blind_position is not None:
            uid = self.table[self.state.small_blind_position]
            return self._strategies.get(uid) if uid else None
        return None

    @property
    def big_blind(self) -> Optional[PlayerLike]:
        """Returns the player currently in the big blind position, or None if no big blind assigned.

        .. versionadded:: 0.3.0
        """
        if self.state.big_blind_position is not None:
            uid = self.table[self.state.big_blind_position]
            return self._strategies.get(uid) if uid else None
        return None

    @property
    def all_stacks_at_game_start(self) -> int:
        """Returns the total of all player stacks at the start of the game.

        .. versionadded:: 0.7.0
        """
        return self._all_stacks_at_game_start

    def _log(
        self,
        message: str,
        loglevel: int = logging.INFO,
        stage_prefix: bool = True,
        **kwargs,
    ) -> None:
        if not self._log_events:  # pragma: no cover
            return

        # ANSI colors (set NO_COLOR=1 to disable)
        color_map = {
            GameStage.PRE_FLOP: "\033[38;5;39m",  # blue
            GameStage.FLOP: "\033[38;5;34m",  # green
            GameStage.TURN: "\033[38;5;214m",  # orange
            GameStage.RIVER: "\033[38;5;196m",  # red
            GameStage.SHOWDOWN: "\033[38;5;201m",  # magenta
        }
        reset = "\033[0m"

        stage = self.state.stage
        stage_name = stage.name
        stage_prefix_msg = f"{color_map.get(stage, '')}{stage_name}{reset}"

        msg = f"{stage_prefix_msg} | {message}" if stage_prefix else message
        self._logger.log(loglevel, msg, **kwargs)

    def subscribe(
        self, event_type: GameEventType, handler: EventHandler, **kwargs
    ) -> str:
        """
        Register a handler for a specific game event type.

        Handlers are called synchronously in registration order when the event occurs.
        Exceptions in handlers are caught, logged, and do not interrupt engine execution.

        Parameters
        ----------
        event_type : GameEventType
            The type of event to listen for.
        handler : EventHandler
            A callable that accepts a GameEvent and returns None.
        """
        return self._events.subscribe(event_type, handler, **kwargs)

    def unsubscribe(self, token: str) -> None:
        """Unsubscribe a handler using its token.

        Parameters
        ----------
        token : str
            The subscription token returned by the subscribe method.
        """
        return self._events.unsubscribe(token)

    def _emit(self, event: GameEvent) -> None:
        """
        Emit a game event to all registered handlers.

        Dispatches the event to handlers in registration order. Exceptions in handlers
        are caught and logged to prevent disruption of engine execution.

        Parameters
        ----------
        event : GameEvent
            The event to emit to handlers.
        """
        self._event_history.append(event)
        if self._save is not None and event.type != GameEventType.GAME_STATE_CHANGED:
            self._save.record(event, self._state)

        # external listeners
        self._events.emit(event, self)

        # player hooks - iterate in snapshot order to preserve deterministic ordering.
        # Players only ever receive their own redacted copy of the event and a
        # PlayerView, never the Game itself.
        for s in self._state.players:
            p = self._strategies.get(s.uid)
            if p is None:
                continue
            target = self._proxies.get(s.uid, p)
            fn = getattr(target, "on_event", None)
            if getattr(fn, "__func__", None) is Player.on_event:
                fn = None  # the default hook does nothing, skip building a view
            specific = getattr(target, f"on_{event.type.name.lower()}", None)
            if not (callable(fn) or callable(specific)):
                continue
            view = self._build_player_view(p)
            if event.type == GameEventType.GAME_STATE_CHANGED:
                player_event = redact_event(
                    event, p.uid, frozenset(self._revealed_uids)
                )
            else:
                player_event = next(
                    e for e in reversed(view.history) if e.uid == event.uid
                )
            if callable(fn):
                try:
                    fn(player_event, view)
                except Exception:
                    self._logger.warning(
                        f"Exception in player {p.name} on_event hook for {event.type.name}",
                        exc_info=True,
                    )
            if callable(specific):
                try:
                    specific(player_event, view)
                except Exception:
                    self._logger.warning(
                        f"Exception in player {p.name} {specific.__name__} hook for {event.type.name}",
                        exc_info=True,
                    )

    def _create_event(
        self,
        event_type: GameEventType,
        player_uid: Optional[str] = None,
        action: Optional[ActionType] = None,
        payload: Optional[dict] = None,
    ) -> GameEvent:
        """
        Create a GameEvent with current game state.

        Parameters
        ----------
        event_type : GameEventType
            The type of event.
        player_uid : Optional[str]
            UID of the player involved in the event.
        action : Optional[ActionType]
            Type of action taken (for PLAYER_ACTION events).

        Returns
        -------
        GameEvent
            An immutable event payload.
        """
        return GameEvent(
            type=event_type,
            hand_number=self.state.hand_number,
            street=self.state.street,
            stage=self.state.stage,
            player_uid=player_uid,
            action=action,
            payload=payload or {},
        )

    def _update_state(self, **changes) -> None:
        has_listeners = self._events.has_subscribers(GameEventType.GAME_STATE_CHANGED)
        before = self.state.model_dump(mode="json") if has_listeners else None
        self._state = self.state.model_copy(update=changes)
        if has_listeners:
            after = self.state.model_dump(mode="json")
            self._emit(
                self._create_event(
                    GameEventType.GAME_STATE_CHANGED,
                    payload={"before": before, "after": after},
                )
            )

    def _update_player_state(self, player, **changes) -> None:
        """Create a new PlayerSnapshot for a player and propagate to game state.

        All PlayerState mutations must go through this method to ensure that
        GAME_STATE_CHANGED is always emitted. A fresh PlayerSnapshot is created
        via model_copy.

        Parameters
        ----------
        player : PlayerLike | PlayerSnapshot
            The player whose state should be updated. Only ``player.uid`` is
            used for the lookup.
        **changes
            Field names and their new values to set on the player's state.
        """
        uid = player.uid
        snapshots = [
            (
                s.model_copy(update={"state": s.state.model_copy(update=changes)})
                if s.uid == uid
                else s
            )
            for s in self._state.players
        ]
        self._update_state(players=snapshots)

    def add_player(
        self, player: PlayerLike, *, state: Optional[PlayerState | dict] = None
    ) -> None:
        """Add a player to the game.

        Parameters
        ----------
        player : PlayerLike
            The player to add to the game.
        state : PlayerState | dict | None, optional
            Initial player state (stack, seat, etc.). If not provided, a default
            ``PlayerState`` with zero chips is used.
        """
        if not self.table.has_free_seat:
            raise ValueError("Table is full")

        if self.state.stage not in [
            GameStage.WAITING_FOR_PLAYERS,
            GameStage.READY,
        ]:
            raise ValueError("Cannot add players while game is in progress")

        existing_names = set([p.name for p in self.state.players])
        if player.name in existing_names:
            raise ValueError(f"Player name '{player.name}' is already taken")

        existing_ids = set([p.uid for p in self.state.players])
        if player.uid in existing_ids:
            raise ValueError(f"Player uid '{player.uid}' is already taken")

        # Normalise state argument
        if isinstance(state, dict):
            initial_player_state = PlayerState.model_validate(state)
        elif isinstance(state, PlayerState):
            initial_player_state = state
        else:
            initial_player_state = PlayerState()

        # Start the worker before changing any state, so a player that can't be
        # isolated is rejected cleanly
        if self._settings.player_isolation == PlayerIsolation.PROCESS:
            proxy = ProcessPlayer(
                player,
                decision_timeout=self._settings.decision_timeout,
                logger=self._logger,
            )
            proxy.start()
            self._proxies[player.uid] = proxy
            self._final_states.pop(player.uid, None)

        # Determine the seat
        preferred_seat = initial_player_state.seat
        try:
            seat_index = self.table.seat_player(player, seat_index=preferred_seat)
        except Exception:
            self._close_proxy(player.uid)
            raise
        initial_player_state = initial_player_state.model_copy(
            update={"seat": seat_index, "state_type": PlayerStateType.ACTIVE}
        )

        snapshot = PlayerSnapshot(
            uid=player.uid,
            name=player.name,
            state=initial_player_state,
        )
        self._strategies[player.uid] = player
        self._update_state(players=[*self.state.players, snapshot])

        self._handle_event(GameEventType.PLAYER_JOINED)
        self._emit(
            self._create_event(GameEventType.PLAYER_JOINED, player_uid=player.uid)
        )
        self._log(
            f"Player {player.name} joined the game.", logging.INFO, stage_prefix=False
        )

    def remove_player(self, player: PlayerLike, flush: bool = True) -> None:
        """Remove a player from the game.

        Parameters
        ----------
        player : PlayerLike
            The player to remove from the game.
        flush : bool
            If True, immediately process the resulting events. If False, the events will be
            added to the queue but not processed until step() is called. Default is True.
        """
        player_uid = player.uid

        if self.state.stage not in [
            GameStage.WAITING_FOR_PLAYERS,
            GameStage.READY,
            GameStage.HAND_COMPLETE,
            GameStage.GAME_OVER,
        ]:
            raise ValueError("Cannot remove players while hand is in progress")

        snapshot = next((p for p in self.state.players if p.uid == player_uid), None)
        if not snapshot:
            raise ValueError(f"Player with uid {player_uid} not found")

        self.table.remove_player(snapshot)
        self._strategies.pop(player_uid, None)
        self._close_proxy(player_uid)
        self._update_state(
            players=[p for p in self.state.players if p.uid != player_uid]
        )

        if flush:
            self._handle_event(GameEventType.PLAYER_LEFT)
        else:
            self._event_queue.append(GameEventType.PLAYER_LEFT)

        # drop the last view held by the player and its redacted history
        if isinstance(player, Player):
            player._view = None
        self._player_histories.pop(player_uid, None)
        self._player_history_synced.pop(player_uid, None)
        self._player_rules.pop(player_uid, None)

        self._emit(self._create_event(GameEventType.PLAYER_LEFT, player_uid=player_uid))
        self._log(
            f"Player {snapshot.name} has left the game.",
            logging.INFO,
            stage_prefix=False,
        )

    def close(self) -> None:
        """Stop the worker processes of isolated players.

        Called automatically when the game ends. Does nothing if no player runs in a
        worker process.

        .. versionadded:: 0.7.0
        """
        for uid in list(self._proxies):
            self._close_proxy(uid)

    def _close_proxy(self, uid: str) -> None:
        proxy = self._proxies.pop(uid, None)
        if proxy is not None:
            proxy.close()
            self._final_states[uid] = proxy.final_state

    def get_player_state(self, player: "PlayerLike | str") -> Optional[dict]:
        """Return the data a player reports through ``export_state``.

        Works the same in both isolation modes. For a player running in a worker
        process, the data is requested from the worker, or, once the worker has
        stopped, taken from its last export. In-process, the player's
        ``export_state`` is called directly. Either way, the result is a copy that
        went through JSON, so it holds no references into the player.

        Parameters
        ----------
        player : PlayerLike | str
            A player object or a plain UID string. Pass the player object for an
            in-process player that has been eliminated or removed.

        Returns
        -------
        dict | None
            The exported data, or ``None`` if the player doesn't implement
            ``export_state`` or its worker failed to answer (a warning is logged).

        Raises
        ------
        ValueError
            If the player is unknown.

        .. versionadded:: 0.7.0
        """
        uid = player if isinstance(player, str) else player.uid
        proxy = self._proxies.get(uid)
        if proxy is not None:
            try:
                return proxy.export_state()
            except PlayerFailure as exc:
                self._logger.warning(
                    f"Could not get the state of player {proxy.name}: {exc}"
                )
                return None
        if uid in self._final_states:
            state = self._final_states[uid]
            return None if state is None else json.loads(json.dumps(state))
        target = self._strategies.get(uid) if isinstance(player, str) else player
        if target is None:
            raise ValueError(f"Player with uid {uid} not found")
        export_state = getattr(target, "export_state", None)
        state = export_state() if callable(export_state) else None
        if state is not None and not isinstance(state, dict):
            raise TypeError(
                f"export_state must return a dict or None, got {type(state).__name__}"
            )
        return None if state is None else json.loads(json.dumps(state))

    def set_player_state(self, player: "PlayerLike | str", state: dict) -> None:
        """Restore a player's state with its ``import_state`` hook.

        The counterpart of :meth:`get_player_state`: passing what it returned restores
        the player. Works the same in both isolation modes. For a player running in a
        worker process, ``import_state`` runs in the worker, on the copy of the player
        that actually plays. The player receives a copy of ``state`` that went through
        JSON.

        Parameters
        ----------
        player : PlayerLike | str
            A player object or a plain UID string.
        state : dict
            JSON-serializable data, typically returned by :meth:`get_player_state`.

        Raises
        ------
        TypeError
            If ``state`` is not a JSON-serializable ``dict``, or an in-process player
            doesn't implement ``import_state``.
        ValueError
            If the player is not in the game.
        RuntimeError
            If an isolated player's worker is not running or fails to restore the
            state.

        .. versionadded:: 0.7.0
        """
        if not isinstance(state, dict):
            raise TypeError(f"state must be a dict, got {type(state).__name__}")
        state = json.loads(json.dumps(state))
        uid = player if isinstance(player, str) else player.uid
        proxy = self._proxies.get(uid)
        if proxy is not None:
            try:
                proxy.import_state(state)
            except PlayerFailure as exc:
                raise RuntimeError(str(exc)) from exc
            return
        if uid in self._final_states:
            raise RuntimeError(
                f"The worker of player {uid} has stopped, so its state can't be set"
            )
        target = self._strategies.get(uid)
        if target is None:
            raise ValueError(f"Player with uid {uid} not found")
        import_state = getattr(target, "import_state", None)
        if not callable(import_state):
            raise TypeError(f"Player {target.name} doesn't implement import_state")
        import_state(state)

    @classmethod
    def load(
        cls,
        save_dir: str | os.PathLike,
        *,
        players: Iterable[PlayerLike],
        max_hands: Optional[int] = None,
        exc_handling_mode: str = "log",
        log_events: bool = True,
        player_isolation: Optional[PlayerIsolation | str] = None,
        decision_timeout: Optional[float] = None,
    ) -> "Game":
        """Load a game saved with ``save_dir``, to continue it with :meth:`start`.

        The game continues from the end of the last completed hand, with the same
        cards it would have dealt had it not been interrupted. The rules, the seed and
        ``first_button_position`` are taken from the save. The loaded game keeps
        appending to the same save; events of a hand that was interrupted are dropped
        from it.

        The save only holds data, never code, so the players must be supplied. They
        must be the players seated at the table when the checkpoint was written, with
        the same UIDs and names. Players that were eliminated don't have to be
        supplied. Each player gets back the state it exported with ``export_state``,
        through its ``import_state`` hook.

        Parameters
        ----------
        save_dir : str | os.PathLike
            The directory the game was saved to.
        players : Iterable[PlayerLike]
            The players at the table.
        max_hands : int | None
            Maximum number of hands, counting those already played. If None, the
            value of the saved game is used. Pass a larger value to continue a game
            that reached its maximum.
        exc_handling_mode, log_events, player_isolation, decision_timeout
            As for :class:`Game`. They are not taken from the save, because they don't
            change the cards or the decisions of deterministic players.

        Returns
        -------
        Game
            The loaded game. Call :meth:`start` to continue it.

        Raises
        ------
        SaveFormatError
            If the save is missing, malformed, or was written in an unsupported
            format version.
        ValueError
            If the players don't match the players at the table.

        Notes
        -----
        Loading never unpickles anything and never imports code named in the save.
        Every file is read as JSON and validated.

        .. versionadded:: 0.7.0
        """
        directory = Path(save_dir)
        header = read_header(directory)
        checkpoint = read_checkpoint(directory)
        if checkpoint.game_uid != header.game_uid:
            raise SaveFormatError(
                "The checkpoint belongs to another game than the header of the save"
            )
        lines = read_event_lines(directory, limit=checkpoint.events)
        if len(lines) < checkpoint.events:
            raise SaveFormatError(
                f"The event log has {len(lines)} complete lines, but the checkpoint "
                f"expects {checkpoint.events}"
            )
        events = [parse_event(line, n) for n, line in enumerate(lines, start=1)]

        game = cls(
            rules=header.rules,
            min_players=header.rules.dealing.min_players,
            max_hands=max_hands if max_hands is not None else header.max_hands,
            exc_handling_mode=exc_handling_mode,
            log_events=log_events,
            first_button_position=header.first_button_position,
            player_isolation=player_isolation,
            decision_timeout=decision_timeout,
            seed=header.seed,
        )
        try:
            game._restore(checkpoint, events, players)
        except BaseException:
            game.close()
            raise
        truncate_event_log(directory, checkpoint.log_size)
        game._save = SaveWriter(directory, events=checkpoint.events)
        return game

    def _restore(
        self,
        checkpoint: Checkpoint,
        events: list[GameEvent],
        players: Iterable[PlayerLike],
    ) -> None:
        """Bring a new game to the state of ``checkpoint``, with ``players`` seated."""
        state = checkpoint.state
        if state.stage not in (GameStage.STARTED, GameStage.HAND_COMPLETE):
            raise SaveFormatError(
                f"The checkpoint was not written between two hands "
                f"(stage {state.stage.name})"
            )
        seats = checkpoint.table.seats
        if len(seats) != len(self._table):
            raise SaveFormatError(
                f"The checkpoint has {len(seats)} seats, but the rules allow "
                f"{len(self._table)} players"
            )
        snapshots = {s.uid: s for s in state.players}
        seated = [uid for uid in seats if uid is not None]
        if len(set(seated)) != len(seated) or any(u not in snapshots for u in seated):
            raise SaveFormatError("The seats of the checkpoint don't match its state")

        supplied: dict[str, PlayerLike] = {}
        for player in players:
            if player.uid in supplied:
                raise ValueError(f"Player uid '{player.uid}' is supplied twice")
            supplied[player.uid] = player
        missing = [snapshots[uid].name for uid in seated if uid not in supplied]
        if missing:
            raise ValueError(
                f"The players at the table must be supplied, missing: "
                f"{', '.join(missing)}"
            )
        unexpected = [p.name for uid, p in supplied.items() if uid not in seated]
        if unexpected:
            raise ValueError(
                f"Only players at the table can be supplied, these are not: "
                f"{', '.join(unexpected)}"
            )
        for uid in seated:
            if supplied[uid].name != snapshots[uid].name:
                raise ValueError(
                    f"Player uid '{uid}' is called {snapshots[uid].name!r} in the "
                    f"save, not {supplied[uid].name!r}"
                )

        rng_version, rng_internal, rng_gauss = checkpoint.rng_state
        try:
            self._rng.setstate((rng_version, tuple(rng_internal), rng_gauss))
        except (TypeError, ValueError) as exc:
            raise SaveFormatError(
                f"The checkpoint holds an invalid random state: {exc}"
            ) from exc

        # Table, with the players in the seats of the checkpoint
        for seat, uid in enumerate(seats):
            if uid is not None:
                self._table.seat_player(supplied[uid], seat_index=seat)
        # The button may be on a seat that was emptied by an elimination, which the
        # setter of Table.button_seat doesn't allow.
        button_seat = checkpoint.table.button_seat
        if button_seat is not None and not 0 <= button_seat < len(seats):
            raise SaveFormatError(
                f"The button is on seat {button_seat}, which is invalid"
            )
        self._table._button_seat = button_seat

        self._state = state
        self._game_uid = checkpoint.game_uid
        self._all_stacks_at_game_start = checkpoint.all_stacks_at_game_start
        self._revealed_uids = set(checkpoint.revealed_uids)
        self._event_history = list(events)

        for uid in seated:
            player = supplied[uid]
            if self._settings.player_isolation == PlayerIsolation.PROCESS:
                proxy = ProcessPlayer(
                    player,
                    decision_timeout=self._settings.decision_timeout,
                    logger=self._logger,
                )
                proxy.start()
                self._proxies[uid] = proxy
            self._strategies[uid] = player

        for uid in seated:
            record = checkpoint.players.get(uid, PlayerRecord())
            if record.export_failed:
                self._logger.warning(
                    f"The state of player {supplied[uid].name} could not be saved, "
                    f"it continues without it."
                )
            elif record.state is not None:
                self.set_player_state(uid, record.state)

        self._resuming = True

    def _create_save(self) -> None:
        """Write the header of the save when the game starts."""
        if self._save is None:
            return
        self._save.create(
            new_header(
                game_uid=self._game_uid,
                rules=self._rules,
                seed=self._seed,
                max_hands=self._max_hands,
                first_button_position=self._first_button_position,
                players=[
                    SeatRecord(uid=p.uid, name=p.name, seat=p.state.seat)
                    for p in self.state.players
                ],
            )
        )

    def _write_checkpoint(self) -> None:
        """Save the events so far and a checkpoint, between two hands."""
        if self._save is None:
            return
        players = {uid: self._export_for_checkpoint(uid) for uid in self._strategies}
        rng_version, rng_internal, rng_gauss = self._rng.getstate()

        def build(events: int, log_size: int) -> Checkpoint:
            return Checkpoint(
                format_version=SAVE_FORMAT_VERSION,
                game_uid=self._game_uid,
                created_at=time.time(),
                events=events,
                log_size=log_size,
                state=self._state,
                table=TableRecord(
                    seats=list(self._table.seats),
                    button_seat=self._table.button_seat,
                ),
                all_stacks_at_game_start=self._all_stacks_at_game_start,
                revealed_uids=sorted(self._revealed_uids),
                rng_state=(rng_version, list(rng_internal), rng_gauss),
                players=players,
            )

        self._save.commit(build)

    def _export_for_checkpoint(self, uid: str) -> PlayerRecord:
        """Export a player's state for a checkpoint. A failure doesn't stop the game."""
        player = self._strategies[uid]
        try:
            proxy = self._proxies.get(uid)
            if proxy is not None:
                state = proxy.export_state()
            else:
                export_state = getattr(player, "export_state", None)
                state = export_state() if callable(export_state) else None
                if state is not None and not isinstance(state, dict):
                    raise TypeError(
                        f"export_state must return a dict or None, "
                        f"got {type(state).__name__}"
                    )
                state = json.loads(json.dumps(state))
        except Exception as exc:
            self._logger.warning(
                f"Could not save the state of player {player.name}, it would continue "
                f"without it if the game is loaded from this checkpoint: {exc}"
            )
            return PlayerRecord(export_failed=True)
        return PlayerRecord(state=state)

    def __enter__(self) -> "Game":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def start(self) -> None:
        """Start the poker game, or continue a game loaded with :meth:`load`.

        .. versionchanged:: 0.7.0
            Continues a loaded game, after emitting a ``GAME_RESUMED`` event.
        """
        if self._resuming:
            self._resuming = False
            self._log("Game resumed.\n", logging.INFO, stage_prefix=False)
            self._emit(self._create_event(GameEventType.GAME_RESUMED))
            self._continue_between_hands()
            self._drain_event_queue()
            return
        self._log("Game started.\n", logging.INFO, stage_prefix=False)
        self._initialize_game()
        self._event_queue.append(GameEventType.GAME_STARTED)
        self._drain_event_queue()

    def _find_first_button_position(self) -> int:
        """Determine the button position (seat index) for the first hand."""
        if isinstance(self._first_button_position, int):
            idx = self._first_button_position % len(self.table)
            self.table.button_seat = idx
            return idx

        if len(self.state.players) == 0:
            raise ValueError("No players to assign button position")

        deck = Deck.standard_deck(shuffle=True, rng=self._rng)
        suit_priority = {
            Suit.SPADES: 3,
            Suit.HEARTS: 2,
            Suit.DIAMONDS: 1,
            Suit.CLUBS: 0,
        }

        best_index = 0  # index in players list
        best_score: tuple[int, int] | None = None

        for idx in range(len(self.state.players)):
            card = deck.deal(1, rng=self._rng)[0]
            score = (card.rank.value, suit_priority[card.suit])

            if best_score is None or score > best_score:
                best_score = score
                best_index = idx

        idx = self.state.players[best_index].state.seat
        self.table.button_seat = idx

        return idx

    def _handle_event(self, event: GameEventType) -> None:
        match event:
            case GameEventType.GAME_STARTED:
                assert self.state.stage == GameStage.READY
                self._update_state(stage=GameStage.STARTED)
                self._game_uid = uuid.uuid4().hex
                self._create_save()
                self._emit(self._create_event(GameEventType.GAME_STARTED))
                self._write_checkpoint()
                self._continue_between_hands()

            case GameEventType.HAND_STARTED:
                assert self.state.stage in [
                    GameStage.STARTED,
                    GameStage.HAND_COMPLETE,
                ]
                self._update_state(stage=GameStage.DEALING)
                self._emit(self._create_event(GameEventType.HAND_STARTED))
                self._deal_hole_cards()
                self._emit(self._create_event(GameEventType.HOLE_CARDS_DEALT))
                self._event_queue.append(GameEventType.HOLE_CARDS_DEALT)

            case GameEventType.HOLE_CARDS_DEALT:
                assert self.state.stage == GameStage.DEALING
                self._post_blinds()
                self._emit(self._create_event(GameEventType.BLINDS_POSTED))
                self._event_queue.append(GameEventType.BLINDS_POSTED)

            case GameEventType.BLINDS_POSTED:
                assert self.state.stage == GameStage.DEALING
                self._post_antes()
                self._emit(self._create_event(GameEventType.ANTES_POSTED))
                self._event_queue.append(GameEventType.ANTES_POSTED)

            case GameEventType.ANTES_POSTED:
                assert self.state.stage == GameStage.DEALING
                self._update_state(stage=GameStage.PRE_FLOP)
                self._emit(self._create_event(GameEventType.BETTING_ROUND_STARTED))
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.PLAYER_ACTION_TAKEN:
                if self.state.is_betting_round_complete:
                    self._complete_betting_round()
                    self._emit(
                        self._create_event(GameEventType.BETTING_ROUND_COMPLETED)
                    )
                    self._event_queue.append(GameEventType.BETTING_ROUND_COMPLETED)
                else:
                    self._advance_to_next_player()
                    self._take_action_from_current_player()
                    self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.BETTING_ROUND_COMPLETED:
                if len(self.state.get_players_in_hand()) == 1:
                    # There is no or only one active player left, so we skip to showdown
                    self._update_state(stage=GameStage.SHOWDOWN, street=None)
                    self._emit(self._create_event(GameEventType.SHOWDOWN_STARTED))
                    self._handle_showdown()
                    self._emit(self._create_event(GameEventType.SHOWDOWN_COMPLETED))
                    self._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)
                else:
                    # There is at least 2 active players, so we continue to next street
                    if self.state.stage == GameStage.PRE_FLOP:
                        self._update_state(stage=GameStage.FLOP, street=Street.FLOP)
                        self._deal_flop()
                        self._emit(self._create_event(GameEventType.FLOP_DEALT))
                        self._event_queue.append(GameEventType.FLOP_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.stage == GameStage.FLOP:
                        self._update_state(stage=GameStage.TURN, street=Street.TURN)
                        self._deal_turn()
                        self._emit(self._create_event(GameEventType.TURN_DEALT))
                        self._event_queue.append(GameEventType.TURN_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.stage == GameStage.TURN:
                        self._update_state(stage=GameStage.RIVER, street=Street.RIVER)
                        self._deal_river()
                        self._emit(self._create_event(GameEventType.RIVER_DEALT))
                        self._event_queue.append(GameEventType.RIVER_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.stage == GameStage.RIVER:
                        self._update_state(stage=GameStage.SHOWDOWN, street=None)
                        self._emit(self._create_event(GameEventType.SHOWDOWN_STARTED))
                        self._handle_showdown()
                        self._emit(self._create_event(GameEventType.SHOWDOWN_COMPLETED))
                        self._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)

            case (
                GameEventType.FLOP_DEALT
                | GameEventType.TURN_DEALT
                | GameEventType.RIVER_DEALT
            ):
                self._emit(self._create_event(GameEventType.BETTING_ROUND_STARTED))
                if self.state.is_betting_round_complete:
                    self._complete_betting_round()
                    self._emit(
                        self._create_event(GameEventType.BETTING_ROUND_COMPLETED)
                    )
                    self._event_queue.append(GameEventType.BETTING_ROUND_COMPLETED)
                    self._log(
                        "There are not active players at the table.",
                        logging.INFO,
                    )
                else:
                    self._take_action_from_current_player()
                    self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.SHOWDOWN_COMPLETED:
                self._update_state(stage=GameStage.HAND_COMPLETE)
                self._emit(self._create_event(GameEventType.HAND_ENDED))
                self._event_queue.append(GameEventType.HAND_ENDED)

            case GameEventType.HAND_ENDED:
                self._log("Hand ended\n", logging.INFO, stage_prefix=False)
                self._eliminate_busted_players()
                self._write_checkpoint()
                self._continue_between_hands()

            case GameEventType.GAME_ENDED:
                self._log("Game ended", logging.INFO, stage_prefix=False)
                self._emit(self._create_event(GameEventType.GAME_ENDED))
                if self._save is not None:
                    self._save.flush()
                self.close()

            case GameEventType.PLAYER_JOINED:
                if self.state.stage == GameStage.WAITING_FOR_PLAYERS:
                    if len(self.state.players) >= self.rules.dealing.min_players:
                        self._update_state(stage=GameStage.READY)

            case GameEventType.PLAYER_LEFT:
                if (
                    len(self.state.get_non_eliminated_players())
                    < self.rules.dealing.min_players
                ):
                    self._update_state(stage=GameStage.WAITING_FOR_PLAYERS)

            case GameEventType.PLAYER_ELIMINATED:
                pass

            case _:  # pragma: no cover
                raise ValueError(f"Unknown event: {event}")

    def _eliminate_busted_players(self) -> None:
        """Eliminate the players who lost their stack in the hand that just ended."""
        # Eliminate players with zero stack
        eliminated_players = [
            p
            for p in self.state.players
            if p.state.stack == 0 and p.state.state_type != PlayerStateType.ELIMINATED
        ]
        for player in eliminated_players:
            self._update_player_state(player, state_type=PlayerStateType.ELIMINATED)
            self._emit(
                self._create_event(
                    GameEventType.PLAYER_ELIMINATED, player_uid=player.uid
                )
            )
            self._log(
                f"Player {player.name} has been eliminated from the game.",
                logging.INFO,
                stage_prefix=False,
            )
            self._event_queue.append(GameEventType.PLAYER_ELIMINATED)
            # Free the table seat and strategy but keep snapshot in state.players
            self.table.remove_player(player)
            self._strategies.pop(player.uid, None)
            self._close_proxy(player.uid)

    def _continue_between_hands(self) -> None:
        """Start the next hand, or end the game.

        Runs between two hands: after the game has started, after a hand has ended,
        and when a loaded game continues.
        """
        if self.state.stage == GameStage.STARTED:
            self._start_new_hand()
            self._event_queue.append(GameEventType.HAND_STARTED)
            return

        # Check if we have enough players to continue
        if (
            len(self.state.get_non_eliminated_players())
            < self.rules.dealing.min_players
        ):
            self._log("Not enough players to continue, ending game.", logging.INFO)
            self._update_state(stage=GameStage.GAME_OVER)
            self._event_queue.append(GameEventType.GAME_ENDED)
        else:
            # Move button and start next hand
            if self.state.hand_number >= self._max_hands:
                self._log(
                    "Reached maximum number of hands, ending game.",
                    logging.INFO,
                    stage_prefix=False,
                )
                self._update_state(stage=GameStage.GAME_OVER)
                self._event_queue.append(GameEventType.GAME_ENDED)
            else:
                self._move_button()
                self._start_new_hand()
                self._event_queue.append(GameEventType.HAND_STARTED)

    def _drain_event_queue(self) -> None:
        while self.step():
            pass

    def step(self) -> bool:
        """Process the next event in the queue."""
        if self.has_events():
            event = self._event_queue.popleft()
            self._handle_event(event)
            return True
        return False

    def has_events(self) -> bool:
        """Check if there are pending events in the queue."""
        return len(self._event_queue) > 0

    def _initialize_game(self) -> None:
        self._update_state(
            hand_number=0,
            button_position=self._find_first_button_position(),
        )

        for p in self.state.players:
            self._all_stacks_at_game_start += p.state.stack

    def _start_new_hand(self) -> None:
        self._update_state(hand_number=self.state.hand_number + 1)

        self._log(
            "=" * 30 + f" Hand {self.state.hand_number} " + "=" * 30 + "\n",
            logging.INFO,
            stage_prefix=False,
        )

        if (
            len(self.state.get_non_eliminated_players())
            < self.rules.dealing.min_players
        ):
            raise ValueError("Not enough players to start hand")

        self._deck = Deck.standard_deck(shuffle=True, rng=self._rng)
        self._revealed_uids.clear()
        self._update_state(
            community_cards=(),
            pot=0,
            current_bet=0,
            last_raise_size=0,
        )

        for player in self.state.players:
            changes = dict(
                current_bet=0,
                total_contributed=0,
                acted_this_street=False,
                holding=None,
            )
            if player.state.stack > 0:
                changes["state_type"] = PlayerStateType.ACTIVE
            self._update_player_state(player, **changes)

        self._update_state(street=Street.PRE_FLOP)

        self._assign_blind_positions()

    def get_current_player(self) -> Optional[PlayerLike]:
        """Return the strategy object for the player whose turn it is.

        .. versionadded:: 0.2.0
        """
        uid = self.table[self.state.current_player_index]
        if uid is None:
            return None
        return self._strategies.get(uid)

    def get_player_snapshot(
        self, player: "PlayerLike | str"
    ) -> Optional[PlayerSnapshot]:
        """Return the current ``PlayerSnapshot`` for a player by UID or player object.

        Parameters
        ----------
        player : PlayerLike | str
            A player object (any object with a ``uid`` attribute) or a plain
            UID string.

        Returns
        -------
        PlayerSnapshot | None
            The frozen snapshot, or ``None`` if no player with that UID is
            currently in the game.

        .. versionadded:: 0.7.0
            Now accepts a ``PlayerLike`` object in addition to a plain UID string.
        """
        uid = player if isinstance(player, str) else player.uid
        return next((s for s in self._state.players if s.uid == uid), None)

    def get_player_view(self, player: "PlayerLike | str") -> PlayerView:
        """Return a fresh :class:`~maverick.playerview.PlayerView` for a player.

        The view contains only the information the player is allowed to observe and
        holds no reference to this game. This is what the engine passes to
        ``decide_action`` and to the event hooks of players.

        Parameters
        ----------
        player : PlayerLike | str
            A player object (any object with a ``uid`` attribute) or a plain
            UID string.

        Returns
        -------
        PlayerView
            The redacted view of the game for the given player.

        .. versionadded:: 0.7.0
        """
        uid = player if isinstance(player, str) else player.uid
        if uid not in self._strategies:
            raise ValueError(f"Player with uid {uid} not found")
        # GAME_STATE_CHANGED events are diagnostics for external listeners that only
        # exist while someone subscribes to them. They are left out of player
        # histories, which keeps those deterministic and cheap; the view itself
        # always carries the current state.
        history = self._player_histories.setdefault(uid, [])
        synced = self._player_history_synced.get(uid, 0)
        for event in self._event_history[synced:]:
            if event.type != GameEventType.GAME_STATE_CHANGED:
                history.append(redact_event(event, uid))
        self._player_history_synced[uid] = len(self._event_history)
        rules = self._player_rules.get(uid)
        if rules is None:
            rules = self._player_rules[uid] = self._rules.model_copy(deep=True)
        return PlayerView(
            player_uid=uid,
            game_uid=self._game_uid,
            state=redact_state(self._state, uid, frozenset(self._revealed_uids)),
            rules=rules,
            history=EventHistoryView(history),
        )

    def _build_player_view(self, player: PlayerLike) -> PlayerView:
        """Build a view for *player* and remember it on ``Player`` instances."""
        view = self.get_player_view(player.uid)
        if isinstance(player, Player):
            player._view = view
        return view

    def _get_snapshot(self, player) -> PlayerSnapshot:
        """Return the snapshot for *player* (which may be PlayerLike or PlayerSnapshot)."""
        return next(s for s in self._state.players if s.uid == player.uid)

    def _calculate_min_raise_amount(self) -> int:
        """Calculates the minimum extra chips the current player must add
        right now to complete a minimum raise.

        Important: What this function returns is NOT the amount the pot needs to raise by
        or raise to, but the amount the player must add on top of their current bet.
        """
        player = self.get_current_player()
        snapshot = self._get_snapshot(player)

        player_bet_before = snapshot.state.current_bet
        old_table_bet = self.state.current_bet
        last_raise_size = self.state.last_raise_size

        min_raise_to = old_table_bet + last_raise_size
        min_raise_by = min_raise_to - player_bet_before

        return min_raise_by

    def _take_action_from_current_player(self) -> None:
        current_player = self.get_current_player()

        if not current_player:
            return

        current_snapshot = self._get_snapshot(current_player)
        if current_snapshot.state.state_type != PlayerStateType.ACTIVE:
            return

        valid_actions = self._get_valid_actions(current_snapshot)
        min_raise_amount = self._calculate_min_raise_amount()

        view = self._build_player_view(current_player)
        decider = self._proxies.get(current_player.uid, current_player)

        _t0 = time.perf_counter()
        try:
            action: PlayerAction = decider.decide_action(
                game=view,
                valid_actions=valid_actions,
                min_raise_amount=min_raise_amount,
                call_amount=self.state.current_bet - current_snapshot.state.current_bet,
                min_bet_amount=self.state.min_bet,
            )
        except PlayerFailure as exc:
            self._log(
                f"Player {current_player.name} failed to decide, folding. {exc}",
                logging.WARNING,
            )
            warn(f"Player {current_player.name} failed to decide, folding.")
            action = PlayerAction(
                player_uid=current_player.uid, action_type=ActionType.FOLD
            )
            self._register_player_action(current_player, action)
            return
        decision_time_seconds = time.perf_counter() - _t0
        # Keep a private copy, so the player can't alter the recorded action later
        action = action.model_copy(deep=True)
        action.decision_time_seconds = decision_time_seconds

        try:
            self._register_player_action(current_player, action)
        except Exception:
            self._log(
                f"Player {current_player.name} intended to take action: {action}.",
                logging.DEBUG,
            )
            self._log(
                f"Player {current_player.name} action invalid, folding.",
                logging.WARNING,
                exc_info=True,
            )
            warn(f"Player {current_player.name} action invalid, folding.")
            action = PlayerAction(
                player_uid=current_player.uid, action_type=ActionType.FOLD
            )
            self._register_player_action(current_player, action)

    def _deal_hole_cards(self) -> None:
        button_uid = self.table[self.state.button_position]
        button_name = self._strategies[button_uid].name if button_uid else "unknown"
        self._log(f"Dealing hole cards. Button: {button_name}", logging.INFO)
        for player in self.state.players:
            if player.state.state_type == PlayerStateType.ACTIVE:
                cards = self._deck.deal(self.rules.dealing.hole_cards, rng=self._rng)
                self._update_player_state(player, holding=Holding(cards=cards))

    def _post_blinds(self) -> None:
        """Post blinds with correct heads-up semantics (button posts SB in HU)."""
        num_players = len(self.state.get_non_eliminated_players())
        min_num_players = self.rules.dealing.min_players

        # Sanity check: ensure we have enough players to post blinds
        if num_players < min_num_players:  # pragma: no cover
            raise ValueError(f"Need at least {min_num_players} players to post blinds")

        # Sanity check: ensure small_blind and big_blind positions are assigned correctly
        if (
            self.state.small_blind_position is None
            or self.state.big_blind_position is None
        ):  # pragma: no cover
            raise ValueError("Small blind or big blind position not assigned")
        if (
            self.state.small_blind_position == self.state.big_blind_position
        ):  # pragma: no cover
            raise ValueError("Small blind and big blind cannot be the same player")

        # --- Small blind ---
        sb_player = self.small_blind
        sb_snapshot = self._get_snapshot(sb_player)
        sb_amount = min(self.state.small_blind, sb_snapshot.state.stack)
        sb_new_stack = sb_snapshot.state.stack - sb_amount
        sb_changes = dict(
            current_bet=sb_amount, total_contributed=sb_amount, stack=sb_new_stack
        )
        if sb_new_stack == 0:
            sb_changes["state_type"] = PlayerStateType.ALL_IN
        self._update_player_state(sb_player, **sb_changes)
        self._update_state(pot=self.state.pot + sb_amount)

        self._log(
            f"Posting small blind of {sb_amount} by player {sb_player.name}. "
            f"Remaining stack: {sb_new_stack}",
            logging.INFO,
        )

        # --- Big blind ---
        bb_player = self.big_blind
        bb_snapshot = self._get_snapshot(bb_player)
        bb_amount = min(self.state.big_blind, bb_snapshot.state.stack)
        bb_new_stack = bb_snapshot.state.stack - bb_amount
        bb_changes = dict(
            current_bet=bb_amount, total_contributed=bb_amount, stack=bb_new_stack
        )
        if bb_new_stack == 0:
            bb_changes["state_type"] = PlayerStateType.ALL_IN
        self._update_player_state(bb_player, **bb_changes)
        self._update_state(pot=self.state.pot + bb_amount)

        self._log(
            f"Posting big blind of {bb_amount} by player {bb_player.name}. "
            f"Remaining stack: {bb_new_stack}",
            logging.INFO,
        )

        # Table betting state
        # IMPORTANT: current_bet should reflect the actual posted BB amount if BB is short-stacked.
        # Next to act preflop:
        # - Heads-up: button (SB) acts first
        # - Multi-way: player left of BB acts first
        if num_players == 2:
            next_player_index = sb_snapshot.state.seat
        else:
            active_uids = {s.uid for s in self._state.get_active_players()}
            next_player_index = self.table.next_occupied_seat(
                bb_snapshot.state.seat, active_uids=active_uids
            )
        self._update_state(
            current_bet=bb_amount,
            min_bet=self.state.big_blind,
            last_raise_size=self.state.big_blind,  # preflop min raise increment is BB size
            current_player_index=next_player_index,
        )

        assert isinstance(
            self.state.current_player_index, int
        ), "Current player index must be an integer"

    def _post_antes(self) -> None:
        """Post antes for all active players."""
        if not self.state.ante or self.state.ante <= 0:
            return

        self._log("Posting antes.", logging.INFO)
        for player in self.state.players:
            if player.state.state_type == PlayerStateType.ACTIVE:
                ante_amount = min(self.state.ante, player.state.stack)
                ante_new_current_bet = player.state.current_bet + ante_amount
                ante_new_total_contributed = (
                    player.state.total_contributed + ante_amount
                )
                ante_new_stack = player.state.stack - ante_amount
                ante_changes = dict(
                    current_bet=ante_new_current_bet,
                    total_contributed=ante_new_total_contributed,
                    stack=ante_new_stack,
                )
                if ante_new_stack == 0:
                    ante_changes["state_type"] = PlayerStateType.ALL_IN
                self._update_player_state(player, **ante_changes)
                self._update_state(pot=self.state.pot + ante_amount)

                self._log(
                    f"Player {player.name} posts ante of {ante_amount}. "
                    f"Remaining stack: {ante_new_stack}",
                    logging.INFO,
                )

    def _calculate_raise_components(
        self, snapshot, chips_to_add: int
    ) -> tuple[int, int, int, int, int, bool]:
        """
        Returns:
            (player_add, player_bet_after, new_table_bet, call_part, raise_size, is_all_in)
        """
        stack_before = snapshot.state.stack
        player_bet_before = snapshot.state.current_bet
        old_table_bet = self.state.current_bet

        player_add = min(chips_to_add, stack_before)
        player_bet_after = player_bet_before + player_add

        # Important: table bet cannot decrease
        new_table_bet = max(old_table_bet, player_bet_after)

        call_needed = max(0, old_table_bet - player_bet_before)
        call_part = min(call_needed, player_add)

        # Amount the table bet increases by (0 if player didn't exceed old_table_bet)
        raise_size = new_table_bet - old_table_bet

        is_all_in = player_add >= stack_before

        return (
            player_add,
            player_bet_after,
            new_table_bet,
            call_part,
            raise_size,
            is_all_in,
        )

    def _reset_acted_flags_for_reopen(self, raiser_id: str) -> None:
        """
        Betting was reopened by a *full* raise (>= last_raise_size).
        Players get re-raise rights back, so we reset acted flags for ACTIVE players
        other than the raiser.
        """
        for p in self.state.players:
            if p.uid != raiser_id and p.state.state_type == PlayerStateType.ACTIVE:
                self._update_player_state(p, acted_this_street=False)

    def _register_player_action(self, player: PlayerLike, action: PlayerAction) -> None:
        action_type = action.action_type
        amount = action.amount or 0

        current_player = self.get_current_player()
        if not current_player or current_player.uid != player.uid:
            raise ValueError("Not this player's turn")

        current_snapshot = self._get_snapshot(current_player)
        if current_snapshot.state.state_type != PlayerStateType.ACTIVE:
            raise ValueError("Player cannot act (folded or all-in)")

        valid_actions = self._get_valid_actions(current_snapshot)
        if action_type not in valid_actions:
            raise ValueError(f"Invalid action: {action_type}")

        if action_type == ActionType.FOLD:
            self._update_player_state(
                current_player,
                state_type=PlayerStateType.FOLDED,
                acted_this_street=True,
            )
            self._log(f"Player {current_player.name} folds.", logging.INFO)

        elif action_type == ActionType.CHECK:
            if current_snapshot.state.current_bet != self.state.current_bet:
                raise ValueError("Cannot check when there is a bet to call")
            self._update_player_state(current_player, acted_this_street=True)
            self._log(f"Player {current_player.name} checks.", logging.INFO)

        elif action_type == ActionType.CALL:
            call_amount = self.state.current_bet - current_snapshot.state.current_bet
            actual_amount = min(call_amount, current_snapshot.state.stack)
            call_new_current_bet = current_snapshot.state.current_bet + actual_amount
            call_new_total_contributed = (
                current_snapshot.state.total_contributed + actual_amount
            )
            call_new_stack = current_snapshot.state.stack - actual_amount
            call_changes = dict(
                current_bet=call_new_current_bet,
                total_contributed=call_new_total_contributed,
                stack=call_new_stack,
                acted_this_street=True,
            )
            if call_new_stack == 0:
                call_changes["state_type"] = PlayerStateType.ALL_IN
            self._update_player_state(current_player, **call_changes)
            self._update_state(pot=self.state.pot + actual_amount)

            self._log(
                f"Player {current_player.name} calls with amount {actual_amount}. Remaining stack: {call_new_stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.BET:
            if self.state.current_bet > 0:
                raise ValueError("Cannot bet when there is already a bet")
            if amount < self.state.min_bet:
                raise ValueError(f"Bet must be at least {self.state.min_bet}")

            actual_amount = min(amount, current_snapshot.state.stack)
            bet_new_total_contributed = (
                current_snapshot.state.total_contributed + actual_amount
            )
            bet_new_stack = current_snapshot.state.stack - actual_amount
            bet_changes = dict(
                current_bet=actual_amount,
                total_contributed=bet_new_total_contributed,
                stack=bet_new_stack,
                acted_this_street=True,
            )
            if bet_new_stack == 0:
                bet_changes["state_type"] = PlayerStateType.ALL_IN
            self._update_player_state(current_player, **bet_changes)
            self._update_state(
                pot=self.state.pot + actual_amount,
                current_bet=actual_amount,
                last_raise_size=actual_amount,
            )

            # A bet opens action for others (everyone else must respond)
            self._reset_acted_flags_for_reopen(raiser_id=current_player.uid)

            self._log(
                f"Player {current_player.name} bets amount {actual_amount}. Remaining stack: {bet_new_stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.RAISE:
            old_table_bet = self.state.current_bet
            old_last_raise_size = self.state.last_raise_size

            (
                player_add,
                player_bet_after,
                new_table_bet,
                _,
                raise_size,
                is_all_in,
            ) = self._calculate_raise_components(current_snapshot, amount)

            if raise_size == 0:
                raise ValueError("RAISE must increase the table bet")

            # Non-all-in raise must meet minimum raise size
            if not is_all_in and raise_size < old_last_raise_size:
                raise ValueError(
                    f"Raise size must be at least {old_last_raise_size} (attempted {raise_size})"
                )

            raise_new_total_contributed = (
                current_snapshot.state.total_contributed + player_add
            )
            raise_new_stack = current_snapshot.state.stack - player_add
            raise_changes = dict(
                current_bet=player_bet_after,
                total_contributed=raise_new_total_contributed,
                stack=raise_new_stack,
                acted_this_street=True,
            )
            if is_all_in:
                raise_changes["state_type"] = PlayerStateType.ALL_IN
            self._update_player_state(current_player, **raise_changes)

            # Reopen betting ONLY on a full raise (>= old_last_raise_size)
            reopens_betting = raise_size >= old_last_raise_size

            if reopens_betting:
                self._update_state(
                    pot=self.state.pot + player_add,
                    current_bet=new_table_bet,
                    last_raise_size=raise_size,
                )
                self._reset_acted_flags_for_reopen(raiser_id=current_player.uid)
            else:
                self._update_state(
                    pot=self.state.pot + player_add,
                    current_bet=new_table_bet,
                )
            # else: short all-in raise does NOT reopen betting and must NOT reset flags

            self._log(
                f"Player {current_player.name} raises by {player_add} chips "
                f"to total bet {player_bet_after}. Remaining stack: {raise_new_stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.ALL_IN:
            old_table_bet = self.state.current_bet
            old_last_raise_size = self.state.last_raise_size

            chips_to_add = current_snapshot.state.stack
            (
                player_add,
                player_bet_after,
                new_table_bet,
                _,
                raise_size,
                _,
            ) = self._calculate_raise_components(current_snapshot, chips_to_add)

            allin_new_total_contributed = (
                current_snapshot.state.total_contributed + player_add
            )
            self._update_player_state(
                current_player,
                current_bet=player_bet_after,
                total_contributed=allin_new_total_contributed,
                stack=0,
                state_type=PlayerStateType.ALL_IN,
                acted_this_street=True,
            )

            # If the all-in increases the table bet, update it
            if new_table_bet > old_table_bet:
                # Reopen betting ONLY if raise_size meets minimum
                reopens_betting = raise_size >= old_last_raise_size
                if reopens_betting:
                    self._update_state(
                        pot=self.state.pot + player_add,
                        current_bet=new_table_bet,
                        last_raise_size=raise_size,
                    )
                    self._reset_acted_flags_for_reopen(raiser_id=current_player.uid)
                else:
                    self._update_state(
                        pot=self.state.pot + player_add,
                        current_bet=new_table_bet,
                    )
                # else: SHORT all-in -> DOES NOT reopen betting -> DO NOT reset acted flags
            else:
                self._update_state(pot=self.state.pot + player_add)

            self._log(
                f"Player {current_player.name} goes all-in with {player_add} chips.",
                logging.INFO,
            )

        self._log(
            f"Current pot: {self.state.pot} | Current bet: {self.state.current_bet}",
            logging.INFO,
        )

        # Emit player action event after all state mutations
        self._emit(
            self._create_event(
                GameEventType.PLAYER_ACTION_TAKEN,
                player_uid=current_player.uid,
                action=action,
            )
        )

    def _get_valid_actions(self, player) -> list[ActionType]:
        """Compute valid actions for *player* (PlayerSnapshot or anything with .state)."""
        actions = [ActionType.FOLD]

        call_amount = self.state.current_bet - player.state.current_bet

        if call_amount == 0:
            actions.append(ActionType.CHECK)
        else:
            if call_amount > 0 and player.state.stack > 0:
                actions.append(ActionType.CALL)

        if self.state.current_bet == 0 and player.state.stack >= self.state.min_bet:
            actions.append(ActionType.BET)

        if self.state.current_bet > 0:
            min_raise_increment = self.state.last_raise_size
            call_amount = self.state.current_bet - player.state.current_bet
            total_needed_for_min_raise = call_amount + min_raise_increment
            if player.state.stack >= total_needed_for_min_raise:
                actions.append(ActionType.RAISE)

        if player.state.stack > 0:
            actions.append(ActionType.ALL_IN)

        return actions

    def _advance_to_next_player(self) -> None:
        """
        Move to the next player who needs to act.

        IMPORTANT:
        A player may have already 'acted_this_street' but still needs to act again
        if they are facing a bet (player.current_bet < table.current_bet). This is
        what makes short all-ins work correctly without resetting acted flags.
        """
        idx = self.state.current_player_index
        starting_idx = idx
        num_players = len(self.table.seats)
        snapshots_by_uid = {s.uid: s for s in self._state.players}

        for _ in range(num_players):
            # get uid at next occupied seat
            idx = self.table.next_occupied_seat(idx)
            uid = self.table[idx]
            s = snapshots_by_uid.get(uid)

            # skip if not active
            if s is None or s.state.state_type != PlayerStateType.ACTIVE:
                continue

            # check if player needs to act
            facing_call = s.state.current_bet < self.state.current_bet
            needs_action = (not s.state.acted_this_street) or facing_call

            if needs_action:
                # Safety check: ensure we've actually moved to a different player
                if idx == starting_idx:  # pragma: no cover
                    # This should not happen in a well-formed game state
                    raise RuntimeError(
                        "Cannot advance to next player: same player would act again"
                    )
                # we've found the next player who needs to act
                self._update_state(current_player_index=idx)
                return

    def _complete_betting_round(self) -> None:
        for player in self.state.players:
            self._update_player_state(player, current_bet=0, acted_this_street=False)
        self._update_state(current_bet=0, last_raise_size=0)
        self._log("Betting round complete\n", logging.INFO)

    def _advance_to_first_active_player(self) -> None:
        active_uids = {s.uid for s in self._state.get_active_players()}
        self._update_state(
            current_player_index=self.table.next_occupied_seat(
                self.state.button_position,
                active_uids=active_uids,
            )
        )

    def _deal_flop(self) -> None:
        self._deck.deal(1, rng=self._rng)
        flop_cards = self._deck.deal(3, rng=self._rng)
        self._update_state(community_cards=(*self.state.community_cards, *flop_cards))
        self._log(
            f"Dealt flop. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )

    def _deal_turn(self) -> None:
        self._deck.deal(1, rng=self._rng)
        turn_card = self._deck.deal(1, rng=self._rng)[0]
        self._update_state(community_cards=(*self.state.community_cards, turn_card))
        self._log(
            f"Dealt turn. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )

    def _deal_river(self) -> None:
        self._deck.deal(1, rng=self._rng)
        river_card = self._deck.deal(1, rng=self._rng)[0]
        self._update_state(community_cards=(*self.state.community_cards, river_card))
        self._log(
            f"Dealt river. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )

    def _move_button(self) -> None:
        self.table.move_button()
        self._update_state(button_position=self.table.button_seat)

    def _assign_blind_positions(self) -> None:
        num_players = len(self.state.get_non_eliminated_players())
        min_num_players = self.rules.dealing.min_players
        if num_players < min_num_players:  # pragma: no cover
            raise ValueError(f"Need at least {min_num_players} players to post blinds")

        # Heads-up special case:
        # - Button is SMALL blind
        # - Other player is BIG blind
        active_uids = {s.uid for s in self._state.get_active_players()}
        if num_players == 2:
            sb_index = self.state.button_position
            bb_index = self.table.next_occupied_seat(sb_index, active_uids=active_uids)
        else:
            # Multi-way:
            # - SB = left of button
            # - BB = left of SB
            sb_index = self.table.next_occupied_seat(
                self.state.button_position, active_uids=active_uids
            )
            bb_index = self.table.next_occupied_seat(sb_index, active_uids=active_uids)
        assert isinstance(sb_index, int)
        assert isinstance(bb_index, int)
        assert sb_index != bb_index, "SB and BB cannot be the same player"

        # Store blind positions in state for easy access by event handlers and player logic
        self._update_state(
            small_blind_position=sb_index,
            big_blind_position=bb_index,
        )

    def _winners_in_button_order(self, winners) -> list:
        n_players = len(self.state.get_non_eliminated_players())
        idx = self.state.button_position  # seat index of the button player
        rel_btn_idx = {}
        for i in range(n_players):
            idx = self.table.next_occupied_seat(idx)
            uid = self.table[idx]
            rel_btn_idx[uid] = i
        return sorted(winners, key=lambda p: rel_btn_idx[p.uid])

    def _handle_showdown(self) -> None:
        players_in_hand = self.state.get_players_in_hand()

        if len(players_in_hand) == 1:
            winner = players_in_hand[0]
            pot_amount = self.state.pot
            self._update_player_state(winner, stack=winner.state.stack + pot_amount)
            self._log(
                f"Player {winner.name} wins {pot_amount} from the pot.",
                logging.INFO,
            )
            self._emit(
                self._create_event(
                    GameEventType.POT_WON,
                    player_uid=winner.uid,
                    payload={"amount": pot_amount},
                )
            )
            self._update_state(pot=0)
        else:
            assert (
                len(self.state.community_cards) == self.rules.dealing.board_cards_total
            ), "Community cards incomplete at multi-player showdown."

            all_contributions = sum(
                [p.state.total_contributed for p in self.state.players]
            )
            assert (
                self.state.pot == all_contributions
            ), f"{self.state.pot} vs {all_contributions}"

            # Calculate best hands and scores for all players in hand
            player_scores: list[tuple[PlayerLike, float]] = []
            for player in players_in_hand:
                if player.state.holding:
                    player_holding = " ".join(
                        card.utf8() for card in player.state.holding.cards
                    )
                    self._log(
                        f"Player {player.name} has holding {player_holding} at showdown,",
                        logging.INFO,
                    )
                    best_hand, best_hand_type, best_score = find_highest_scoring_hand(
                        private_cards=player.state.holding.cards,
                        community_cards=self.state.community_cards,
                        n_private=self.rules.showdown.hole_cards_required,
                    )
                    player_scores.append((player, best_score))

                    # the holding becomes public information from now on
                    self._revealed_uids.add(player.uid)
                    self._emit(
                        self._create_event(
                            GameEventType.PLAYER_CARDS_REVEALED,
                            player_uid=player.uid,
                            payload={
                                "holding": [
                                    card.code() for card in player.state.holding.cards
                                ],
                                "best_hand": [card.code() for card in best_hand],
                                "best_hand_type": best_hand_type.name,
                                "best_score": best_score,
                            },
                        )
                    )
                    self._log(
                        (
                            f"Player {player.name} has hand {best_hand_type.name} with "
                            f"cards {[card.utf8() for card in best_hand]}"
                            f" (score: {best_score:.8g})"
                        ),
                        logging.INFO,
                    )

            score_by_id = {p.uid: s for p, s in player_scores}
            players_in_hand_ids = {p.uid for p in players_in_hand}

            # Record total contributions for pot distribution
            contributions = {
                p.uid: p.state.total_contributed for p in self.state.players
            }
            contribution_levels = sorted(
                {amt for amt in contributions.values() if amt > 0}
            )

            # Distribute pot based on contributions (handles side pots)
            pot_to_distribute = self.state.pot
            awards = {p.uid: 0 for p in self.state.players}
            previous_level = 0
            for level in contribution_levels:
                segment_contributors = [
                    p for p in self.state.players if contributions[p.uid] >= level
                ]
                delta = level - previous_level
                segment_amount = delta * len(segment_contributors)
                previous_level = level

                # eligibility: must have contributed enough AND not folded
                eligible = [
                    p for p in segment_contributors if p.uid in players_in_hand_ids
                ]

                if not eligible:  # pragma: no cover
                    # should never happen in a sane game, but don't crash silently
                    raise RuntimeError("No eligible players for a pot segment.")

                # Deduct distributed segment from pot
                self._update_state(pot=self.state.pot - segment_amount)

                if len(segment_contributors) == 1:
                    # uncalled top layer -> refund to that one contributor
                    lone = segment_contributors[0]
                    awards[lone.uid] += segment_amount
                    continue

                # determine winners among eligible for THIS segment
                best = max(score_by_id[p.uid] for p in eligible)
                segment_winners = [p for p in eligible if score_by_id[p.uid] == best]

                share, rem = divmod(segment_amount, len(segment_winners))

                # distribute shares
                for w in segment_winners:
                    awards[w.uid] += share

                # distribute remainder in relative button order
                segment_winners_sorted = self._winners_in_button_order(segment_winners)
                for i in range(rem):
                    idx = i % len(segment_winners_sorted)
                    awards[segment_winners_sorted[idx].uid] += 1

            # Sanity check if the pot is fully distributed
            assert (
                self.state.pot == 0
            ), f"Pot should be fully distributed, {self.state.pot} remaining."

            # Pay out awards to winners
            pot_distributed = 0
            id_to_player = {p.uid: p for p in self.state.players}
            for p_id in awards:
                amount = awards[p_id]
                if amount == 0:
                    continue
                player = id_to_player[p_id]
                self._update_player_state(player, stack=player.state.stack + amount)
                pot_distributed += amount
                self._log(
                    f"Player {player.name} wins {amount} from the pot.", logging.INFO
                )
                self._emit(
                    self._create_event(
                        GameEventType.POT_WON,
                        player_uid=player.uid,
                        payload={"amount": amount},
                    )
                )

            # Final sanity check
            assert pot_distributed == pot_to_distribute

        # Sanity check
        total_stacks = sum(p.state.stack for p in self.state.players)
        if not total_stacks == self._all_stacks_at_game_start:  # pragma: no cover
            raise RuntimeError(
                "Total chips in game do not match initial amount after showdown."
            )

        self._log("Showdown complete\n", logging.INFO)
