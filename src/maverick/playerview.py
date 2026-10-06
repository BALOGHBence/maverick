"""
Information-safe, per-seat view of a game.

Players never receive the live :class:`~maverick.game.Game` instance. Instead, the engine
hands them a :class:`PlayerView`, which contains only what a real player sitting at the
table could observe: public table state, their own hole cards, hole cards that have been
revealed at showdown, and the (redacted) event history.
"""

import copy
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, overload

from .enums import GameEventType
from .events import GameEvent
from .holding import Holding
from .playeraction import ClosedDict
from .playerstate import PlayerSnapshot
from .rules import PokerRules
from .state import GameState

if TYPE_CHECKING:  # pragma: no cover
    from .protocol import PlayerLike

__all__ = ["PlayerView", "EventHistoryView", "redact_state", "redact_event"]


def _is_hidden(uid: str, viewer_uid: str, revealed: frozenset[str]) -> bool:
    return uid != viewer_uid and uid not in revealed


def redact_state(
    state: GameState, viewer_uid: str, revealed: frozenset[str] = frozenset()
) -> GameState:
    """Return a copy of ``state`` as observed by the player ``viewer_uid``.

    The holdings of all other players are removed, except for those who revealed
    their cards at showdown.

    Parameters
    ----------
    state : GameState
        The full game state.
    viewer_uid : str
        The UID of the observing player.
    revealed : frozenset[str], optional
        UIDs of players whose holdings are public. Default is an empty set.

    Returns
    -------
    GameState
        A redacted copy that shares no mutable objects with ``state``.

    .. versionadded:: 0.7.0
    """
    # Everything in a GameState is immutable, except for the list of players and
    # the list of cards in a holding, so only those need to be copied.
    players = []
    for p in state.players:
        holding = p.state.holding
        if holding is not None:
            if _is_hidden(p.uid, viewer_uid, revealed):
                holding = None
            else:
                holding = holding.model_copy(update={"cards": list(holding.cards)})
            p = p.model_copy(
                update={"state": p.state.model_copy(update={"holding": holding})}
            )
        players.append(p)
    return state.model_copy(update={"players": players})


def _copy_payload(obj: Any) -> Any:
    """Deep copy an event payload.

    Payloads are JSON-like data, for which copying the dicts and lists directly is
    much faster than ``copy.deepcopy``. Anything else falls back to ``copy.deepcopy``.
    """
    if type(obj) in (dict, ClosedDict):
        return type(obj)({k: _copy_payload(v) for k, v in obj.items()})
    if type(obj) is list:
        return [_copy_payload(v) for v in obj]
    if obj is None or type(obj) in (str, int, float, bool):
        return obj
    return copy.deepcopy(obj)


def _redact_state_dump(dump: Any, viewer_uid: str, revealed: frozenset[str]) -> Any:
    """Redact holdings in a ``GameState.model_dump(mode="json")`` dictionary in place."""
    if not isinstance(dump, dict):
        return dump
    for player in dump.get("players") or []:
        state = player.get("state") or {}
        if state.get("holding") is not None and _is_hidden(
            player.get("uid"), viewer_uid, revealed
        ):
            state["holding"] = None
    return dump


def redact_event(
    event: GameEvent, viewer_uid: str, revealed: frozenset[str] = frozenset()
) -> GameEvent:
    """Return a deep copy of ``event`` as observed by the player ``viewer_uid``.

    Only ``GAME_STATE_CHANGED`` events carry private information (the serialized
    ``before`` and ``after`` game states). In those, the holdings of all other players
    are removed, except for those who revealed their cards at showdown. All other
    event types are public and are only copied.

    Parameters
    ----------
    event : GameEvent
        The original event.
    viewer_uid : str
        The UID of the observing player.
    revealed : frozenset[str], optional
        UIDs of players whose holdings were public when the event was emitted.
        Default is an empty set.

    Returns
    -------
    GameEvent
        A redacted deep copy that shares no mutable objects with ``event``.

    .. versionadded:: 0.7.0
    """
    update: dict[str, Any] = {"payload": _copy_payload(event.payload)}
    if event.action is not None:
        update["action"] = event.action.model_copy(
            update={"payload": _copy_payload(event.action.payload)}
        )
    redacted = event.model_copy(update=update)
    if event.type == GameEventType.GAME_STATE_CHANGED:
        for key in ("before", "after"):
            if key in redacted.payload:
                _redact_state_dump(redacted.payload[key], viewer_uid, revealed)
    return redacted


class EventHistoryView(Sequence[GameEvent]):
    """A read-only, fixed-length window over a player's redacted event history.

    Creating the window is O(1), so the engine can hand out a fresh view on every
    decision and every event without copying the whole history.

    .. versionadded:: 0.7.0
    """

    __slots__ = ("_events", "_length")

    def __init__(self, events: list[GameEvent], length: Optional[int] = None) -> None:
        self._events = events
        self._length = len(events) if length is None else length

    @overload
    def __getitem__(self, index: int) -> GameEvent: ...  # pragma: no cover

    @overload
    def __getitem__(
        self, index: slice
    ) -> tuple[GameEvent, ...]: ...  # pragma: no cover

    def __getitem__(self, index: int | slice) -> GameEvent | tuple[GameEvent, ...]:
        if isinstance(index, slice):
            return tuple(self._events[: self._length][index])
        if index < 0:
            index += self._length
        if not 0 <= index < self._length:
            raise IndexError("history index out of range")
        return self._events[index]

    def __len__(self) -> int:
        return self._length

    def __repr__(self) -> str:
        return f"EventHistoryView(len={self._length})"


@dataclass(frozen=True, slots=True)
class PlayerView:
    """A read-only view of a game from the perspective of a single player.

    This is what players receive as the ``game`` argument of
    :meth:`~maverick.player.Player.decide_action` and of their event hooks. It exposes
    only information a real player at the table could observe:

    - the public table state (pot, bets, stacks, positions, community cards, ...),
    - the viewer's own hole cards,
    - hole cards of other players only after they have been revealed at showdown,
    - the game rules,
    - the event history, with private information removed.

    The deck, the strategy objects of other players and the engine internals are not
    reachable from a ``PlayerView``. Everything it holds is a copy, so modifying it has
    no effect on the game.

    Fields
    ------
    player_uid : str
        UID of the player this view belongs to.
    game_uid : Optional[str]
        UID of the game session, or ``None`` before the game has started.
    state : GameState
        Redacted copy of the current game state.
    rules : PokerRules
        Copy of the rules of the game.
    history : Sequence[GameEvent]
        The redacted event history in chronological order.

    .. versionadded:: 0.7.0
    """

    player_uid: str
    game_uid: Optional[str]
    state: GameState
    rules: PokerRules
    history: Sequence[GameEvent]

    @classmethod
    def from_state(
        cls,
        *,
        player_uid: str,
        state: GameState,
        rules: PokerRules,
        game_uid: Optional[str] = None,
        history: Sequence[GameEvent] = (),
        revealed: frozenset[str] = frozenset(),
    ) -> "PlayerView":
        """Create a view from full (unredacted) data.

        Useful for testing a player strategy without running a game. The state and the
        history are redacted for ``player_uid``, and everything is copied.
        """
        return cls(
            player_uid=player_uid,
            game_uid=game_uid,
            state=redact_state(state, player_uid, revealed),
            rules=rules.model_copy(deep=True),
            history=EventHistoryView(
                [redact_event(e, player_uid, revealed) for e in history]
            ),
        )

    @property
    def uid(self) -> Optional[str]:
        """Alias for ``game_uid``, mirroring :attr:`Game.uid <maverick.game.Game.uid>`."""
        return self.game_uid

    @property
    def me(self) -> Optional[PlayerSnapshot]:
        """The snapshot of the player this view belongs to."""
        return self.get_player_snapshot(self.player_uid)

    @property
    def holding(self) -> Optional[Holding]:
        """The hole cards of the player this view belongs to, if any."""
        me = self.me
        return me.state.holding if me is not None else None

    def get_player_snapshot(
        self, player: "PlayerLike | str"
    ) -> Optional[PlayerSnapshot]:
        """Return the (redacted) ``PlayerSnapshot`` for a player by UID or player object.

        Parameters
        ----------
        player : PlayerLike | str
            A player object (any object with a ``uid`` attribute) or a plain
            UID string.

        Returns
        -------
        PlayerSnapshot | None
            The snapshot, or ``None`` if no player with that UID is in the game.
        """
        uid = player if isinstance(player, str) else player.uid
        return next((s for s in self.state.players if s.uid == uid), None)
