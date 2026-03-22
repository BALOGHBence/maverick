import time
from typing import Optional
import uuid
import warnings

from pydantic import BaseModel, Field

from .card import Card
from .enums import (
    GameStage,
    PlayerStateType,
    Street,
)
from .playerstate import PlayerSnapshot

__all__ = ["GameState"]


class GameState(BaseModel):
    """
    Represents the complete state of a Texas Hold'em game.

    This class encapsulates all information about the current state of the game,
    including players, community cards, pot, and betting information.

    Fields
    ------
    uid : str
        Unique identifier for the event. This is automatically set to a new UUID by default.
        
        .. versionadded:: 0.7.0
    ts: float
        Timestamp of when the event was created, in seconds since the epoch.
        This is automatically set to the current time when the class is instantiated.
        
        .. versionadded:: 0.7.0
    stage : GameStage
        The current state of the game (e.g., WAITING_FOR_PLAYERS, IN_PROGRESS).

        .. versionadded:: 0.2.0
    street : Optional[Street]
        The current betting round (e.g., PRE_FLOP, FLOP, TURN, RIVER).
    players : list[PlayerSnapshot]
        The list of player snapshots in the game. Each snapshot is an immutable
        record of observable player data (uid, name, state) at the time the
        ``GameState`` was created. Live strategy objects are held separately
        in ``Game._strategies``.

        .. versionchanged:: 0.8.0
            Type changed from ``list[PlayerLike]`` to ``list[PlayerSnapshot]``.
    current_player_index : Optional[int]
        The index of the player whose turn it is to act.
    community_cards : tuple[Card, ...]
        The community cards on the table.
    pot : int
        The total amount of chips in the pot.
    current_bet : int
        The current highest bet that players need to match.
    min_bet : int
        The minimum bet amount for the current betting round.
    last_raise_size : int
        The size of the last raise made in the current betting round.
    small_blind : int
        The amount of the small blind.
    big_blind : int
        The amount of the big blind.
    ante : int
        The ante amount for the game.
    hand_number : int
        The current hand number in the game.
    button_position : Optional[int]
        The position (seat index) of the dealer button at the table.
    small_blind_position : Optional[int]
        The position (seat index) of the small blind at the table.

        .. versionadded:: 0.3.0
    big_blind_position : Optional[int]
        The position (seat index) of the big blind at the table.

        .. versionadded:: 0.3.0
    """
    
    uid: str = Field(default_factory=lambda: uuid.uuid4().hex, alias="id")
    ts: float = Field(default_factory=time.time)

    stage: GameStage = GameStage.WAITING_FOR_PLAYERS
    street: Optional[Street] = None
    players: list[PlayerSnapshot] = Field(default_factory=list)
    current_player_index: Optional[int] = None

    # Cards
    community_cards: tuple[Card, ...] = Field(default_factory=tuple)

    # Betting
    pot: int = 0
    current_bet: int = 0
    min_bet: int = 0
    last_raise_size: int = 0  # Tracks the minimum raise increment (last bet/raise size)
    small_blind: int = Field(default=10, ge=1)
    big_blind: int = Field(default=20, ge=1)
    ante: int = Field(default=0, ge=0)

    # Hand tracking
    hand_number: int = 0
    button_position: Optional[int] = None
    small_blind_position: Optional[int] = None
    big_blind_position: Optional[int] = None

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
        "populate_by_name": True,
    }

    @property
    def state_type(self) -> GameStage:
        """Get the current game state type.

        .. deprecated:: 0.2.0
            Use `stage` attribute instead.
        """
        warnings.warn(
            "'state_type' is deprecated and will be removed in v1.0.0; use stage 'instead'.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.stage

    def get_active_players(self) -> list[PlayerSnapshot]:
        """Return list of player snapshots who haven't folded and have chips."""
        return [
            p
            for p in self.players
            if p.state.state_type == PlayerStateType.ACTIVE and p.state.stack > 0
        ]

    def get_players_in_hand(self) -> list[PlayerSnapshot]:
        """Return list of player snapshots still in the hand (not folded)."""
        return [
            p
            for p in self.players
            if p.state.state_type in [PlayerStateType.ACTIVE, PlayerStateType.ALL_IN]
        ]

    @property
    def is_betting_round_complete(self) -> bool:
        """Betting round is complete when no further action is possible/required."""
        in_hand = self.get_players_in_hand()

        # If only one player remains, hand is effectively over
        if len(in_hand) <= 1:
            return True

        can_act = self.get_active_players()

        # If less than 2 players can act, betting is complete
        if len(can_act) < 2:
            return True

        # Everyone who can act must have acted since the last reopen
        if not all(p.state.acted_this_street for p in can_act):
            return False

        # Everyone who can act must have matched the current bet
        if not all(p.state.current_bet == self.current_bet for p in can_act):
            return False

        return True
