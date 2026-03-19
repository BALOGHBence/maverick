import warnings
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import ActionType

__all__ = ["PlayerAction"]


class PlayerAction(BaseModel):
    """Represents an action taken by a player during their turn in a game.

    Fields
    ------
    player_uid : str
        Unique identifier of the player taking the action. Replaces deprecated ``player_id``.
    action_type : ActionType
        Type of action being taken.
    amount : Optional[int]
        Amount for BET or RAISE. None for CALL, CHECK, or FOLD.
        IMPORTANT: The amount is always the value that you want to
        put into the pot from your stack, NOT the total bet/raise amount
        after the action is taken.
    payload : dict[str, Any]
        Additional action-specific data.

        .. versionadded:: 0.6.0
    decision_time_seconds : Optional[float]
        Time in seconds it took the player to make the decision.
        Automatically populated by the game engine when the action is taken.

        .. versionadded:: 0.6.0
    """

    model_config = ConfigDict(populate_by_name=True)

    player_uid: str = Field(
        ...,
        alias="player_id",
        description="Unique identifier of the player taking the action.",
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

    payload: dict[str, Any] = Field(default_factory=dict)
    decision_time_seconds: Optional[float] = Field(
        default=None,
        description="Time in seconds it took the player to make the decision.",
    )

    @model_validator(mode="before")
    @classmethod
    def _warn_on_player_id(cls, data):
        if isinstance(data, dict) and "player_id" in data and "player_uid" not in data:
            warnings.warn(
                "PlayerAction 'player_id' parameter is deprecated, use 'player_uid' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return data

    @property
    def player_id(self) -> str:
        """Deprecated: use ``player_uid`` instead."""
        warnings.warn(
            "PlayerAction.player_id is deprecated, use PlayerAction.player_uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.player_uid
