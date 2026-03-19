import warnings
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .enums import ActionType

__all__ = ["PlayerAction"]


class PlayerAction(BaseModel):
    """Represents an action taken by a player during their turn in a game.

    Fields
    ------
    player_uid : str
        Unique identifier of the player taking the action.
    action_type : ActionType
        Type of action being taken.
    amount : Optional[int]
        Amount for BET or RAISE. None for CALL, CHECK, or FOLD.
        IMPORTANT: The amount is always the value that you want to
        put into the pot from your stack, NOT the total bet/raise amount
        after the action is taken.
    """

    player_uid: str = Field(
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

    @model_validator(mode="before")
    @classmethod
    def _handle_deprecated_player_id(cls, data: object) -> object:
        if isinstance(data, dict) and "player_id" in data and "player_uid" not in data:
            warnings.warn(
                "PlayerAction.player_id is deprecated, use player_uid instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            data = dict(data)
            data["player_uid"] = data.pop("player_id")
        return data

    @property
    def player_id(self) -> str:
        """Deprecated alias for player_uid.

        .. deprecated::
            Use :attr:`player_uid` instead.
        """
        warnings.warn(
            "PlayerAction.player_id is deprecated, use player_uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.player_uid
