import warnings
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Optional
import uuid

from .enums import ActionType
from .playeraction import PlayerAction
from .playerstate import PlayerState
from ._registered_players import registered_players

if TYPE_CHECKING:  # pragma: no cover
    from .events import GameEvent
    from .playerview import PlayerView

__all__ = ["Player"]

# Registry for classes by their cls_uid
_uid_registry: dict[str, type["Player"]] = {}


class PlayerMeta(ABCMeta):

    def __init__(self, name, bases, namespace, *args, **kwargs):
        super().__init__(name, bases, namespace, *args, **kwargs)

    def __new__(metaclass, name, bases, namespace, *args, **kwargs):
        cls = super().__new__(metaclass, name, bases, namespace, *args, **kwargs)
        if not ABC in bases and getattr(cls, "register", True):
            registered_players[cls.__name__] = cls
            # Register by cls_uid if it exists
            cls_uid = getattr(cls, "cls_uid", None)
            if cls_uid is not None:
                _uid_registry[cls_uid] = cls
        return cls


class Player(metaclass=PlayerMeta):
    """Abstract base class for a poker player."""

    register: bool = True
    cls_uid: Optional[str] = None

    def __init__(
        self,
        *,
        uid: Optional[str] = None,
        name: str,
        **kwargs,
    ):
        _id = kwargs.pop("id", None)
        if _id:
            warnings.warn(
                "Passing id= to Player.__init__ is deprecated, use uid= instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.uid = uid or _id or uuid.uuid4().hex
        self.name = name
        self._view: "Optional[PlayerView]" = None

    @property
    def id(self) -> str:
        """Deprecated: use ``uid`` instead."""
        warnings.warn(
            "Player.id is deprecated, use Player.uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.uid

    @property
    def game(self) -> Optional["PlayerView"]:
        """The most recent view of the game this player received, or None.

        The engine refreshes this view right before calling :meth:`decide_action` and
        the event hooks, so it is current inside those methods. Outside of them it
        reflects the game as of the player's last decision or event.

        .. versionchanged:: 0.7.0
            Returns a :class:`~maverick.playerview.PlayerView` instead of the live
            :class:`~maverick.game.Game` instance.
        """
        return self._view

    @property
    def state(self) -> Optional["PlayerState"]:
        """The state of the player as of the most recent view of the game."""
        if self._view is None:
            return None
        snapshot = self._view.me
        return snapshot.state if snapshot is not None else None

    @classmethod
    def get_by_uid(cls, uid: str) -> Optional[type["Player"]]:
        """
        Get a player class by its unique identifier.

        Parameters
        ----------
        uid : str
            The unique identifier of the player class.

        Returns
        -------
        Optional[type[Player]]
            The player class with the given uid, or None if not found.
        """
        return _uid_registry.get(uid)

    @abstractmethod
    def decide_action(
        self,
        *,
        game: "PlayerView",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        """
        Decide on an action to take during the player's turn.

        The function should return a valid instance of PlayerAction.

        Parameters
        ----------
        game : PlayerView
            A read-only view of the game from this player's perspective. It contains
            the public game state, the player's own hole cards, the rules and the
            event history, but not the deck or the hole cards of other players.

            .. versionchanged:: 0.7.0
                A :class:`~maverick.playerview.PlayerView` is passed instead of the
                live :class:`~maverick.game.Game` instance.
        valid_actions : list[ActionType]
            List of valid actions the player can take.
        min_raise_amount : int
            Minimum extra chips this player must add right now to complete a minimum raise.
        call_amount : int
            Amount of chips this player must add right now to call the current bet.
        min_bet_amount : int
            Minimum chips this player must add right now to make a bet.

        Returns
        -------
        PlayerAction
            An instance of PlayerAction representing the chosen action.
        """
        ...

    def on_event(
        self, event: "GameEvent", game: "PlayerView"
    ) -> None:  # pragma: no cover
        """
        Optional hook called when a game event occurs.

        This method is called synchronously after global event handlers.
        Exceptions in this method are caught and logged by the engine.

        Parameters
        ----------
        event : GameEvent
            The game event that occurred, with private information removed.
        game : PlayerView
            A read-only view of the game from this player's perspective.

            .. versionchanged:: 0.7.0
                A :class:`~maverick.playerview.PlayerView` is passed instead of the
                live :class:`~maverick.game.Game` instance.

        Notes
        -----
        This is an optional hook. The default implementation does nothing.
        Subclasses can override this method to observe events.
        """
        ...

    def export_state(self) -> Optional[dict[str, Any]]:
        """
        Optional hook that returns the state of the player.

        Together with :meth:`import_state` this forms a pair: ``export_state`` returns
        everything needed to restore the player later, as a JSON-serializable
        ``dict``, and ``import_state`` restores it. Typical contents are statistics
        the player collects while it plays, opponent models, or the cost of calls to
        an external service. Leave out secrets such as API keys and anything that can
        be recreated, such as clients.

        :meth:`Game.get_player_state <maverick.game.Game.get_player_state>` reads it.
        This matters most for players isolated in worker processes: the player object
        there is a copy, so attributes it changes while playing are not visible on the
        object passed to :meth:`Game.add_player <maverick.game.Game.add_player>`. The
        returned data is sent to the engine as JSON, so it is the only way to get data
        out of an isolated player. The engine reads it one last time when the worker
        stops, so it stays available after the game has ended.

        Returns
        -------
        dict | None
            JSON-serializable data, or ``None`` (the default) if the player has no
            state worth keeping.

        .. versionadded:: 0.7.0
        """
        return None

    def import_state(self, state: dict[str, Any]) -> None:
        """
        Optional hook that restores a state returned by :meth:`export_state`.

        :meth:`Game.set_player_state <maverick.game.Game.set_player_state>` calls it.
        For players isolated in worker processes, it runs in the worker, on the copy
        of the player that actually plays.

        Parameters
        ----------
        state : dict
            A copy of data previously returned by :meth:`export_state`, after a round
            trip through JSON.

        .. versionadded:: 0.7.0
        """
        return None
