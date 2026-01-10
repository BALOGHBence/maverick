from typing import Optional

from pydantic import BaseModel

from .enums import ActionType
from .state import GameState
from .playeraction import PlayerAction
from .playerstate import PlayerState

__all__ = ["Player"]


class Player(BaseModel):
    """A player's state during a poker game."""

    id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[PlayerState] = None

    def decide_action(
        self,
        game_state: GameState,
        valid_actions: list[ActionType],
        min_raise: int,  # noqa: ARG002
    ) -> PlayerAction:
        """
        Decide on an action to take during the player's turn.

        The function should return a valid instance of PlayerAction.
        """
        raise NotImplementedError(
            "decide_action method must be implemented by subclasses."
        )
