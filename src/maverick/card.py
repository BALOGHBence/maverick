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
