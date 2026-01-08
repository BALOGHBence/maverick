from typing import Optional

from pydantic import BaseModel, Field

from .card import Card
from .deck import Deck
from .enums import (
    GameStateType,
    PlayerState,
    Street,
)
from .protocol import PlayerLike

__all__ = ["GameState"]


class GameState(BaseModel):
    """
    Represents the complete state of a Texas Hold'em game.

    This class encapsulates all information about the current state of the game,
    including players, community cards, pot, and betting information.
    """

    state_type: GameStateType = GameStateType.WAITING_FOR_PLAYERS
    street: Street = Street.PRE_FLOP
    players: list[PlayerLike] = Field(default_factory=list)
    active_players: list[int] = Field(default_factory=list)  # Indices of active players
    current_player_index: int = 0
    dealer_index: int = 0

    # Cards
    deck: Optional[Deck] = None
    community_cards: list[Card] = Field(default_factory=list)

    # Betting
    pot: int = 0
    current_bet: int = 0
    min_bet: int = 0
    small_blind: int = Field(default=10, ge=1)
    big_blind: int = Field(default=20, ge=1)

    # Hand tracking
    hand_number: int = 0
    button_position: int = 0
    
    model_config = {
        "arbitrary_types_allowed": True,
    }

    def get_active_players(self) -> list[PlayerLike]:
        """Return list of players who haven't folded and have chips."""
        return [
            p for p in self.players if p.state == PlayerState.ACTIVE and p.stack > 0
        ]

    def get_players_in_hand(self) -> list[PlayerLike]:
        """Return list of players still in the hand (not folded)."""
        return [p for p in self.players if p.state != PlayerState.FOLDED]

    def get_current_player(self) -> Optional[PlayerLike]:
        """Return the player whose turn it is."""
        if 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def is_betting_round_complete(self) -> bool:
        """Check if the current betting round is complete."""
        active = self.get_active_players()

        # If only one player left, betting is complete
        if len(self.get_players_in_hand()) <= 1:
            return True

        # All players must have acted
        if not all(p.acted_this_street for p in active):
            return False

        # All active players must have equal bets or be all-in
        for player in active:
            if (
                player.state != PlayerState.ALL_IN
                and player.current_bet != self.current_bet
            ):
                return False

        return True
