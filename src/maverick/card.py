import random
from typing import Tuple

from pydantic import BaseModel

from .enums import Suit, Rank, HandType
from .utils.scoring import score_hand


__all__ = ["Card"]


class Card(BaseModel):
    """A playing card with a suit and rank.

    Fields
    ------
    suit : Suit
        The suit of the card (Hearts, Diamonds, Clubs, Spades).
    rank : Rank
        The rank of the card (Two through Ace).

    Examples
    --------
    >>> from maverick import Card, Suit, Rank
    >>> card = Card(suit=Suit.HEARTS, rank=Rank.ACE)
    >>> card.utf8()
    'A♥'
    """

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

    def score(self) -> Tuple[HandType, float]:
        """Classifies and scores the card.

        Returns (HandType, float_score) where higher scores = stronger hands.
        """
        return score_hand([self])

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

    def code(self) -> str:
        """Return short canonical card code (e.g. Ah, Td, Ks)."""
        rank_codes = {
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "T",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }
        suit_codes = {
            Suit.HEARTS: "h",
            Suit.DIAMONDS: "d",
            Suit.CLUBS: "c",
            Suit.SPADES: "s",
        }
        return f"{rank_codes[self.rank]}{suit_codes[self.suit]}"

    def text(self) -> str:
        """Return human-readable text representation."""
        return f"{self.rank.name.title()} of {self.suit.name.title()}"

    def __repr__(self) -> str:
        return f"Card({self.code()})"

    def __str__(self) -> str:
        return self.utf8()
