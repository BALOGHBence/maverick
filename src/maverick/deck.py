from warnings import warn
import random

from pydantic import BaseModel

from .enums import Suit, Rank
from .card import Card

__all__ = ["Deck"]


class Deck(BaseModel):
    """A standard deck of 52 playing cards.

    Parameters
    ----------
    cards : list[Card]
        The list of cards in the deck.

    Examples
    --------
    >>> from maverick import Deck
    >>> deck = Deck.standard_deck(shuffle=True)
    >>> dealt_cards = deck.deal(5)
    >>> len(dealt_cards)
    5
    >>> len(deck.cards)
    47
    """

    cards: list[Card]

    @classmethod
    def build(cls, shuffle: bool = False) -> "Deck":
        """Build a standard deck of 52 cards.

        Parameters
        ----------
        shuffle : bool, optional
            Whether to shuffle the deck after building (default is False).
        """
        ranks = list(Rank)
        suits = list(Suit)
        cards = []

        for rank in ranks:
            for suit in suits:
                card = Card(suit=suit, rank=rank)
                cards.append(card)

        deck = cls(cards=cards)

        if shuffle:
            deck.shuffle()

        return deck

    @classmethod
    def standard_deck(cls, shuffle: bool = False) -> "Deck":
        """Create and optionally shuffle a standard deck of 52 cards.

        This is an alias for Deck.build() for clarity.

        Parameters
        ----------
        shuffle : bool, optional
            Whether to shuffle the deck after building (default is False).
        """
        return cls.build(shuffle=shuffle)

    def deal(self, n: int) -> list[Card]:
        """
        Deal n random cards from the deck.

        Parameters
        ----------
        n : int
            The number of cards to deal.

        Returns
        -------
        list[Card]
            The list of dealt cards.

        Raises
        ------
        ValueError
            If there are not enough cards in the deck to deal.

        Notes
        -----
        1) Dealt cards are removed from the deck.
        2) If n <= 0, an empty list is returned.
        """
        if n > len(self.cards):
            raise ValueError("Not enough cards in the deck to deal.")

        if n <= 0:
            warn(
                "Requested to deal non-positive number of cards; returning empty list."
            )
            return []

        dealt_cards = random.sample(self.cards, n)

        for card in dealt_cards:
            self.cards.remove(card)

        return dealt_cards

    def shuffle(self, n: int = 1) -> None:
        """Shuffle the deck of cards n times.

        Parameters
        ----------
        n : int, optional
            The number of times to shuffle the deck (default is 1).
        """
        if n <= 0:
            warn("Number of shuffles must be positive; returning unshuffled deck.")
            return self

        for _ in range(n):
            random.shuffle(self.cards)

        return self
