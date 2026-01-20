from typing import Optional

from pydantic import BaseModel, Field

from .enums import ActionType

__all__ = ["PlayerAction"]


class PlayerAction(BaseModel):
    """Represents an action taken by a player during their turn in a game.

    Fields
    ------
    player_id : str
        Unique identifier of the player taking the action.
    action_type : ActionType
        Type of action being taken.
    amount : Optional[int]
        Amount for BET or RAISE. None for CALL, CHECK, or FOLD.
        IMPORTANT: The amount is always the value that you want to
        put into the pot from your stack, NOT the total bet/raise amount
        after the action is taken.
    """

    player_id: str = Field(
        ..., description="Unique identifier of the player taking the action."
    )
    action_type: ActionType = Field(..., description="Type of action being taken.")
    amount: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Amount for BET or RAISE. None for CALL, CHECK, or FOLD. "
            "IMPORTANT: The amount is always the value that you want to "
            "put into the pot from your stack, NOT the total bet amount "
            "after the action is taken."
        ),
    )
