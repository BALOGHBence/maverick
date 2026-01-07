from pydantic import BaseModel
from .enums import Suit, Rank
import random

from .card import Card

__all__ = ["Deck"]


class Deck(BaseModel):
    """A standard deck of 52 playing cards."""

    cards: list[Card]

    @classmethod
    def build(cls) -> "Deck":
        """Build a standard deck of 52 cards."""
        ranks = list(Rank)
        suits = list(Suit)
        cards = []
        for rank in ranks:
            for suit in suits:
                card = Card(suit=suit, rank=rank)
                cards.append(card)
        return cls(cards=cards)

    @classmethod
    def standard_deck(cls, shuffle: bool = False) -> "Deck":
        """Create and optionally shuffle a standard deck of 52 cards."""
        deck = cls.build()
        if shuffle:
            deck.shuffle()
        return deck

    def deal(self, n: int) -> list[Card]:
        """Deal n random cards from the deck."""
        dealt_cards = random.sample(self.cards, n)
        for card in dealt_cards:
            self.cards.remove(card)
        return dealt_cards

    def shuffle(self, n: int = 1) -> None:
        """Shuffle the deck of cards n times."""
        for _ in range(n):
            random.shuffle(self.cards)
        return self
