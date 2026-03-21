"""
Game event model for the synchronous event dispatch system.

This module defines an immutable GameEvent payload that represents
a snapshot of what happened in the game at a specific point in time.
"""

import time
import uuid
import warnings
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import GameEventType, Street, GameStage
from .playeraction import PlayerAction

__all__ = ["GameEvent"]


class GameEvent(BaseModel):
    """
    Immutable game event payload.

    Represents a snapshot of a game event that occurred, including
    the type of event, current game state, and relevant action details.

    Payload by event type:
    - PLAYER_CARDS_REVEALED:
        - holding: list[str] - The player's hole cards as a list of card codes.
        - best_hand: list[str] - The best hand the player can make as a list of card codes.
        - best_hand_type: str - The type of the best hand (e.g., "FLUSH") according to HandType.
        - best_score: float - The score of the best hand the player can make.

        .. versionadded:: 0.2.0

    Fields
    ------
    type : GameEventType
        The type of event that occurred.
    hand_number : int
        The current hand number.
    street : Optional[Street]
        The current betting street.
    stage : Optional[GameStage]
        The current game stage.

        .. versionadded:: 0.2.0
    uid : str
        Unique identifier for the event. Replaces deprecated ``id``.
    ts: float
        Timestamp of when the event was created, in seconds since the epoch.
    player_uid : Optional[str]
        UID of the player involved in the event, if applicable. Replaces deprecated ``player_id``.
    action : Optional[PlayerAction]
        The action taken by the player, if applicable.
    payload : dict[str, Any]
        Additional event-specific data.
    """

    uid: str = Field(default_factory=lambda: uuid.uuid4().hex, alias="id")
    ts: float = Field(default_factory=time.time)
    type: GameEventType

    hand_number: int
    street: Optional[Street] = None
    stage: Optional[GameStage] = None

    player_uid: Optional[str] = Field(default=None, alias="player_id")
    action: Optional[PlayerAction] = None

    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _warn_on_deprecated_params(cls, data):
        if isinstance(data, dict):
            if "id" in data and "uid" not in data:
                warnings.warn(
                    "GameEvent 'id' parameter is deprecated, use 'uid' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            if "player_id" in data and "player_uid" not in data:
                warnings.warn(
                    "GameEvent 'player_id' parameter is deprecated, use 'player_uid' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
        return data

    model_config = ConfigDict(
        frozen=True,  # Makes the model immutable
        extra="forbid",  # Prevents accidental fields
        arbitrary_types_allowed=True,
        populate_by_name=True,  # Allow both uid= and id= in constructor
    )

    @property
    def id(self) -> str:
        """Deprecated: use ``uid`` instead."""
        warnings.warn(
            "GameEvent.id is deprecated, use GameEvent.uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.uid

    @property
    def player_id(self) -> Optional[str]:
        """Deprecated: use ``player_uid`` instead."""
        warnings.warn(
            "GameEvent.player_id is deprecated, use GameEvent.player_uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.player_uid
