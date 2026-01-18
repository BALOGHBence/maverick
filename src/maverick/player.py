from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import uuid

from .enums import ActionType
from .playeraction import PlayerAction
from .playerstate import PlayerState

if TYPE_CHECKING:  # pragma: no cover
    from .game import Game
    from .events import GameEvent

__all__ = ["Player"]


class Player(ABC):
    """Abstract base class for a poker player."""
    
    def __init__(self, *, id: Optional[str] = None, name: Optional[str] = None, state: Optional[PlayerState] = None):
        self.id = id or uuid.uuid4().hex
        self.name = name
        self.state = state

    @abstractmethod
    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        min_call_amount: int,
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
        min_raise : int
            Minimum raise-by increment (chips to add on top of call amount).
            For RAISE actions, the amount should be at least this value.

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
