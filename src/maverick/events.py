"""
Game event model for the synchronous event dispatch system.

This module defines an immutable GameEvent payload that represents
a snapshot of what happened in the game at a specific point in time.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from .enums import GameEventType, Street, ActionType

__all__ = ["GameEvent"]


class GameEvent(BaseModel):
    """
    Immutable game event payload.

    Represents a snapshot of a game event that occurred, including
    the type of event, current game state, and relevant action details.

    Attributes
    ----------
    type : GameEventType
        The type of event that occurred.
    hand_number : int
        The current hand number.
    street : Street
        The current betting street.
    player_id : Optional[str]
        ID of the player involved in the event, if applicable.
    action : Optional[ActionType]
        Type of action taken, if applicable (for PLAYER_ACTION events).
    amount : Optional[int]
        Amount involved in the action, if applicable.
    pot : int
        Current pot size.
    current_bet : int
        Current bet amount on the table.
    """

    type: GameEventType
    hand_number: int
    street: Street
    player_id: Optional[str] = None
    action: Optional[ActionType] = None
    amount: Optional[int] = None
    pot: int
    current_bet: int

    model_config = ConfigDict(
        frozen=True,  # Makes the model immutable
        extra="forbid",  # Prevents accidental fields
        arbitrary_types_allowed=True,
    )
