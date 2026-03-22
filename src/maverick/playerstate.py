from typing import Optional

from pydantic import BaseModel, Field

from .enums import PlayerStateType
from .holding import Holding

__all__ = ["PlayerState", "PlayerSnapshot"]


class PlayerState(BaseModel):
    """A player's state during a poker game.

    Fields
    ------
    seat : Optional[int]
        The seat number of the player at the table.
    state_type : Optional[PlayerStateType]
        The type of player state (e.g., ACTIVE, FOLDED, ALL_IN).
    stack : int
        The number of chips the player has.
    holding : Optional[Holding]
        The player's private cards.
    current_bet : int
        The amount the player has contributed in the current betting round.
    total_contributed : int
        The total amount the player has contributed in the current hand.
    acted_this_street : bool
        Whether the player has acted in the current betting round.
    """

    model_config = {"frozen": True}

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


class PlayerSnapshot(BaseModel):
    """An immutable snapshot of observable player data at a point in time.

    Separates observable state from strategy logic. ``GameState.players`` holds
    a list of these snapshots; the live strategy objects are stored separately
    inside ``Game._strategies``.

    Fields
    ------
    uid : str
        Unique identifier for the player instance.
    name : str
        Display name of the player.
    state : PlayerState
        Frozen player state (seat, stack, holding, bets, etc.).

    .. versionadded:: 0.7.0
    """

    model_config = {"frozen": True}

    uid: str
    name: str
    state: PlayerState
