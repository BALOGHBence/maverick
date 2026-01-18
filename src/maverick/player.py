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

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        name: str,
        state: Optional[PlayerState] = None,
    ):
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
