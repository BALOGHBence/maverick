"""
Game event model for the synchronous event dispatch system.

This module defines an immutable GameEvent payload that represents
a snapshot of what happened in the game at a specific point in time.
"""

import warnings
from typing import Optional, Any
import time, uuid

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
    player_uid : Optional[str]
        UID of the player involved in the event, if applicable.
    action : Optional[PlayerAction]
        The action taken by the player, if applicable.
    payload : dict[str, Any]
        Additional event-specific data.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = Field(default_factory=time.time)
    type: GameEventType

    hand_number: int
    street: Optional[Street] = None
    stage: Optional[GameStage] = None

    player_uid: Optional[str] = None
    action: Optional[PlayerAction] = None

    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        frozen=True,  # Makes the model immutable
        extra="forbid",  # Prevents accidental fields
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _handle_deprecated_player_id(cls, data: object) -> object:
        if isinstance(data, dict) and "player_id" in data and "player_uid" not in data:
            warnings.warn(
                "GameEvent.player_id is deprecated, use player_uid instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            data = dict(data)
            data["player_uid"] = data.pop("player_id")
        return data

    @property
    def player_id(self) -> Optional[str]:
        """Deprecated alias for player_uid.

        .. deprecated::
            Use :attr:`player_uid` instead.
        """
        warnings.warn(
            "GameEvent.player_id is deprecated, use player_uid instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.player_uid
