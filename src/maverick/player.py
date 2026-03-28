import warnings
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Optional
import uuid

from .enums import ActionType
from .playeraction import PlayerAction
from .playerstate import PlayerState
from ._registered_players import registered_players

if TYPE_CHECKING:  # pragma: no cover
    from .game import Game
    from .events import GameEvent

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
        self._game: "Optional[Game]" = None

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
    def game(self) -> Optional["Game"]:
        """Get the game instance this player is currently in, or None if not in a game."""
        return self._game
    
    @property
    def state(self) -> Optional["PlayerState"]:
        """Get the current state of the player."""
        if self.game is None:
            return None
        # Find the player's state in the game state by matching uid
        for snapshot in self.game.state.players:
            if snapshot.uid == self.uid:
                return snapshot.state
        return None

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
        game: "Game",
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
        game : Game
            The game instance containing the current state.
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

    def on_event(self, event: "GameEvent", game: "Game") -> None:  # pragma: no cover
        """
        Optional hook called when a game event occurs.

        This method is called synchronously after global event handlers.
        Exceptions in this method are caught and logged by the engine.

        Parameters
        ----------
        event : GameEvent
            The game event that occurred.
        game : Game
            The game instance containing the current state.

        Notes
        -----
        This is an optional hook. The default implementation does nothing.
        Subclasses can override this method to observe events.
        """
        ...

    def to_dict(self) -> dict:
        """
        Serialize the player to a dictionary.

        Returns
        -------
        dict
            A dictionary representation of the player.
        """
        return {
            "uid": self.uid,
            "name": self.name,
        }
