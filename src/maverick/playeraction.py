from typing import Optional

from pydantic import BaseModel, Field

from .enums import ActionType

__all__ = ["PlayerAction"]


class PlayerAction(BaseModel):
    """Represents an action taken by a player during their turn."""

    player_id: Optional[str] = None
    action_type: ActionType = Field(...)
    amount: Optional[int] = Field(default=None, ge=0)
