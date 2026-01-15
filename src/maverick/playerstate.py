from typing import Optional

from pydantic import BaseModel, Field

from .enums import PlayerStateType
from .holding import Holding

__all__ = ["PlayerState"]


class PlayerState(BaseModel):
    """A player's state during a poker game."""

    # Identity / seating
    seat: Optional[int] = Field(default=None, ge=0)
    state_type: Optional[PlayerStateType] = None

    # Chips / cards
    stack: int = Field(default=0, ge=0)
    holding: Optional[Holding] = None

    # Hand / betting-round state
    current_bet: int = Field(
        default=0, ge=0
    )  # contribution in the current betting round
    total_contributed: int = Field(default=0, ge=0)  # total contribution this hand
    acted_this_street: bool = False
