from typing import Optional

from pydantic import BaseModel, Field

from .enums import PlayerState, ActionType
from .holding import Holding
from .state import GameState
from .playeraction import PlayerAction

__all__ = ["Player"]


class Player(BaseModel):
    """A player's state during a poker game."""

    # Identity / seating
    id: Optional[str] = None
    name: Optional[str] = None
    seat: Optional[int] = Field(default=None, ge=0)
    state: Optional[PlayerState] = None

    # Chips / cards
    stack: int = Field(default=0, ge=0)
    holding: Optional[Holding] = None

    # Hand / betting-round state
    current_bet: int = Field(
        default=0, ge=0
    )  # contribution in the current betting round
    total_contributed: int = Field(default=0, ge=0)  # total contribution this hand
    acted_this_street: bool = False

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """
        Decide on an action to take during the player's turn.

        The function should return a valid instance of PlayerAction.
        """
        raise NotImplementedError(
            "decide_action method must be implemented by subclasses."
        )
