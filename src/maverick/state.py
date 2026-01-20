from typing import Optional, Any

from pydantic import BaseModel, Field, field_serializer, field_validator

from .card import Card
from .deck import Deck
from .enums import (
    GameStateType,
    PlayerStateType,
    Street,
)
from .protocol import PlayerLike
from ._registered_players import registered_players

__all__ = ["GameState"]


class GameState(BaseModel):
    """
    Represents the complete state of a Texas Hold'em game.

    This class encapsulates all information about the current state of the game,
    including players, community cards, pot, and betting information.

    Fields
    ------
    state_type : GameStateType
        The current state of the game (e.g., WAITING_FOR_PLAYERS, IN_PROGRESS).
    street : Street
        The current betting round (e.g., PRE_FLOP, FLOP, TURN, RIVER).
    players : list[PlayerLike]
        The list of players in the game.
    active_players : list[int]
        Indices of players who are still active in the current hand.
    current_player_index : int
        The index of the player whose turn it is to act.
    deck : Optional[Deck]
        The deck of cards used in the game.
    community_cards : list[Card]
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
    button_position : int
        The position of the dealer button at the table.
    """

    state_type: GameStateType = GameStateType.WAITING_FOR_PLAYERS
    street: Street = Street.PRE_FLOP
    players: list[PlayerLike] = Field(default_factory=list)
    active_players: list[int] = Field(default_factory=list)  # Indices of active players
    current_player_index: int = 0

    # Cards
    deck: Optional[Deck] = None
    community_cards: list[Card] = Field(default_factory=list)

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
    button_position: int = 0

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @field_serializer("players")
    def _ser_players(self, players: list[PlayerLike]) -> list[dict]:
        result = []
        for p in players:
            d = p.to_dict()
            d["__class__.__name__"] = p.__class__.__name__
            result.append(d)
        return result

    @field_validator("players", mode="before")
    @classmethod
    def _parse_players(cls, players: list[Any]) -> list[PlayerLike]:
        result = []
        for p in players:
            if isinstance(p, PlayerLike):
                # accept already-built objects
                result.append(p)
            else:
                # re-instantiate from dict
                if not "__class__.__name__" in p:
                    raise KeyError(
                        "Serialized player data missing '__class__.__name__' key"
                    )

                cls = registered_players[p["__class__.__name__"]]
                if not cls:
                    raise ValueError(
                        f"Unrecognized player class '{p['__class__.__name__']}'"
                    )

                result.append(cls(**p))

        return result

    def get_active_players(self) -> list[PlayerLike]:
        """Return list of players who haven't folded and have chips."""
        return [
            p
            for p in self.players
            if p.state.state_type == PlayerStateType.ACTIVE and p.state.stack > 0
        ]

    def get_players_in_hand(self) -> list[PlayerLike]:
        """Return list of players still in the hand (not folded)."""
        return [p for p in self.players if p.state.state_type != PlayerStateType.FOLDED]

    def get_current_player(self) -> Optional[PlayerLike]:
        """Return the player whose turn it is."""
        if 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def is_betting_round_complete(self) -> bool:
        """Betting round is complete when no further action is possible/required."""
        in_hand = [
            p for p in self.players if p.state.state_type != PlayerStateType.FOLDED
        ]

        # If only one player remains, hand is effectively over
        if len(in_hand) <= 1:
            return True

        can_act = [p for p in in_hand if p.state.state_type == PlayerStateType.ACTIVE]

        # If nobody can act (everyone left is all-in), betting is complete
        if not can_act:
            return True

        # Everyone who can act must have acted since the last reopen
        if not all(p.state.acted_this_street for p in can_act):
            return False

        # Everyone who can act must have matched the current bet
        if not all(p.state.current_bet == self.current_bet for p in can_act):
            return False

        return True
