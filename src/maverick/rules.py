from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import Street, GameVariant

__all__ = [
    "DealingRules",
    "StakesRules",
    "PokerRules",
]


class DealingRules(BaseModel):
    """
    Rules related to seating limits and how cards are dealt.

    Fields
    ------
    variant
        Which game is played (Hold'em, Omaha, ...). This can influence hole-card
        count, evaluation logic, and potentially board layout.
    max_players
        Maximum number of seats allowed at the table. Typical values:
        - 6 for "6-max"
        - 9 for "full ring"
    min_players
        Minimum number of active players required to start a new hand. In most
        poker games, 2 is the minimum (heads-up).

    hole_cards
        Number of private cards dealt to each player at the start of a hand.
        - Hold'em: 2
        - Omaha: 4 (commonly)
    board_cards_total
        Total number of community cards dealt by the end of the hand.
        - Hold'em / Omaha: 5
        - Some games have 0 community cards.

    board_deal_pattern
        How board cards are revealed over the streets, expressed as a dictionary mapping
        Street to int.

        For standard Hold'em:
        {
            Street.PREFLOP: 0,
            Street.FLOP: 3,
            Street.TURN: 1,
            Street.RIVER: 1,
        }
        meaning:
            - preflop: 0 board cards dealt (only hole cards)
            - flop:    3 board cards
            - turn:    1 board card
            - river:   1 board card

        This pattern also implicitly defines how many betting rounds exist if you
        align each entry with one "street".
    """

    variant: GameVariant = GameVariant.TEXAS_HOLDEM
    max_players: int = Field(default=9, ge=2, le=10)
    min_players: int = Field(default=2, ge=2, le=10)

    hole_cards: int = Field(default=2, ge=1, le=4)
    board_cards_total: int = Field(default=5, ge=0, le=5)

    board_deal_pattern: dict[Street, int] = {
        Street.PRE_FLOP: 0,
        Street.FLOP: 3,
        Street.TURN: 1,
        Street.RIVER: 1,
    }


class StakesRules(BaseModel):
    """
    Rules related to blinds, antes, and straddles (forced or optional preflop bets).

    Fields
    ------
    small_blind
        The small blind amount. This is a forced bet posted by the player left
        of the button in standard games.
    big_blind
        The big blind amount. This is a forced bet posted by the player left of
        the small blind, and it typically defines:
        - the price to call preflop
        - the default minimum opening bet/raise (in no-limit/pot-limit)
    ante
        The ante amount. This is a forced bet posted by all players before the hand starts.
    """

    small_blind: int = Field(..., ge=0)
    big_blind: int = Field(..., gt=0)
    ante: int = Field(default=0, ge=0)


class PokerRules(BaseModel):
    """
    Full configuration for a poker game.

    This config is intended to be:
    - serializable (store it in hand histories, reproduce games deterministically)
    - explicit (no hidden defaults beyond what you set here)
    - reusable (same rules can be applied across many games)

    Fields
    ------
    name
        Human-readable label for the ruleset (e.g., "NLHE Cash 1/2", "PLO").
        Useful for logs, exports, and UI.
    dealing
        Card dealing and seating-related rules (variant, hole cards, board pattern, etc.).
    stakes
        Blind/ante/straddle rules.
    betting
        Bet sizing and raising structure rules.

    rules_version
        Version tag for the rules schema.
    """

    name: str = "NLHE"
    dealing: DealingRules
    stakes: StakesRules

    rules_version: str = "1.0"
