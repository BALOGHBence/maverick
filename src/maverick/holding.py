from typing import Optional
import random
from itertools import combinations

from pydantic import BaseModel

from .card import Card
from .deck import Deck

__all__ = ["Holding"]


class Holding(BaseModel):
    """Two cards held by a player."""

    cards: list[Card]

    @classmethod
    def random(cls, deck: Optional[Deck] = None):
        if deck:
            cards = random.sample(deck.cards, 2)
        else:
            cards = Card.random(2)
        return cls(cards=cards)

    @classmethod
    def all_possible_holdings(cls, cards: list[Card], n: int = 2) -> iter:
        """Generate all possible holdings of n cards from the given deck."""
        for combination in combinations(cards, n):
            yield cls(cards=list(combination))
