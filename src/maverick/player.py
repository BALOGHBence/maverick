from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

from .enums import ActionType
from .playeraction import PlayerAction
from .playerstate import PlayerState

if TYPE_CHECKING:
    from .game import Game
    from .events import GameEvent

__all__ = ["Player"]


class Player(BaseModel):
    """A player's state during a poker game."""

    id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[PlayerState] = None

    def decide_action(
        self,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise: int,  # noqa: ARG002
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
        raise NotImplementedError(
            "decide_action method must be implemented by subclasses."
        )

    def on_event(self, event: "GameEvent") -> None:
        """
        Optional hook called when a game event occurs.

        This method is called synchronously after global event handlers.
        It allows players to observe game events without affecting engine logic.
        Exceptions in this method are caught and logged by the engine.

        Parameters
        ----------
        event : GameEvent
            The game event that occurred.

        Notes
        -----
        This is an optional hook. The default implementation does nothing.
        Subclasses can override this method to observe events.
        """
        pass
