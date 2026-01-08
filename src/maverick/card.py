from pydantic import BaseModel
from .enums import Suit, Rank
import random

__all__ = ["Card"]


class Card(BaseModel):
    """A playing card with a suit and rank."""

    suit: Suit
    rank: Rank

    @classmethod
    def random(cls, n: int = 1) -> list["Card"]:
        """Generate n random cards without repetition."""
        suits = list(Suit)
        ranks = list(Rank)
        all_cards = [cls(suit=s, rank=r) for s in suits for r in ranks]
        selected = random.sample(all_cards, n)
        return selected if n > 1 else selected[0]
    
    def utf8(self) -> str:
        """Return the UTF-8 representation of the card."""
        suit_symbols = {
            Suit.HEARTS: "♥",
            Suit.SPADES: "♠",
            Suit.CLUBS: "♣",
            Suit.DIAMONDS: "♦",
        }
        rank_symbols = {
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "10",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }
        return f"{rank_symbols[self.rank]}{suit_symbols[self.suit]}"
