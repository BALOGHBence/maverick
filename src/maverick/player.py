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


class PlayerMeta(ABCMeta):

    def __init__(self, name, bases, namespace, *args, **kwargs):
        super().__init__(name, bases, namespace, *args, **kwargs)

    def __new__(metaclass, name, bases, namespace, *args, **kwargs):
        cls = super().__new__(metaclass, name, bases, namespace, *args, **kwargs)
        if not ABC in bases and getattr(cls, "register", True):
            registered_players[cls.__name__] = cls
        return cls


class Player(metaclass=PlayerMeta):
    """Abstract base class for a poker player."""

    register: bool = True

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        name: str,
        state: Optional[PlayerState | dict] = None,
        **_,
    ):
        self.id = id or uuid.uuid4().hex
        self.name = name
        self.state = (
            state
            if isinstance(state, PlayerState) or state is None
            else PlayerState.model_validate(state)
        )

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
            "id": self.id,
            "name": self.name,
            "state": self.state.model_dump() if self.state else None,
        }
