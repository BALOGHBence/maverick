"""
Game event model for the synchronous event dispatch system.

This module defines an immutable GameEvent payload that represents
a snapshot of what happened in the game at a specific point in time.
"""

from typing import Optional, Any
import time, uuid

from pydantic import BaseModel, ConfigDict, Field

from .enums import GameEventType, Street
from .playeraction import PlayerAction

__all__ = ["GameEvent"]


class GameEvent(BaseModel):
    """
    Immutable game event payload.

    Represents a snapshot of a game event that occurred, including
    the type of event, current game state, and relevant action details.

    Fields
    ------
    type : GameEventType
        The type of event that occurred.
    hand_number : int
        The current hand number.
    street : Street
        The current betting street.
    player_id : Optional[str]
        ID of the player involved in the event, if applicable.
    action : Optional[PlayerAction]
        The action taken by the player, if applicable.
    payload : dict[str, Any]
        Additional event-specific data.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = Field(default_factory=time.time)
    type: GameEventType

    hand_number: int
    street: Street

    player_id: Optional[str] = None
    action: Optional[PlayerAction] = None

    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        frozen=True,  # Makes the model immutable
        extra="forbid",  # Prevents accidental fields
        arbitrary_types_allowed=True,
    )
