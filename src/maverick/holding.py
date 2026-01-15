from typing import Optional, Tuple
import random
from itertools import combinations

from pydantic import BaseModel

from .card import Card
from .deck import Deck
from .utils import estimate_holding_strength, score_hand
from .enums import HandType

__all__ = ["Holding"]


class Holding(BaseModel):
    """A number of cards held by a player.

    Examples
    --------
    >>> from maverick import Holding, Card
    ... pair_of_aces = Holding(cards=[
    ...     Card(suit='S', rank=14),  # Ace of Spades
    ...     Card(suit='H', rank=14)   # Ace of Hearts
    ... ])
    >>> pair_of_aces.estimate_strength(n_simulations=1000, n_players=8)
    0.85  # Example output, actual value may vary
    """

    cards: list[Card]

    @classmethod
    def random(cls, *, n: int = 2, deck: Optional[Deck] = None) -> "Holding":
        """Generate a random holding of 2 cards.

        Parameters
        ----------
        n : int, optional
            The number of cards in the holding (default is 2).
        deck : Deck, optional
            An optional deck to draw cards from. If not provided, random cards will be
            generated.
        """
        if deck:
            cards = random.sample(deck.cards, n)
        else:
            cards = Card.random(n=n)
        return cls(cards=cards)

    @classmethod
    def all_possible_holdings(cls, cards: list[Card], n: int = 2) -> iter:
        """Generate all possible holdings of n cards from the given deck.

        Parameters
        ----------
        cards : list[Card]
            The list of cards to choose from.
        n : int, optional
            The number of cards in each holding (default is 2).
        """
        for combination in combinations(cards, n):
            yield cls(cards=list(combination))

    def score(self) -> Tuple[HandType, float]:
        """Classifies and scores the hand.

        Returns (HandType, float_score) where higher scores = stronger hands.
        """
        return score_hand(self.cards)

    def estimate_strength(self, **kwargs) -> float:
        """
        Estimate the strength of the holding via Monte Carlo simulation.

        Returns a number between 0 and 1, representing the probability of the current hand
        being the strongest.

        The keyword arguments are passed to `estimate_holding_strength`.
        """
        return estimate_holding_strength(holding=self.cards, **kwargs)

    def __repr__(self) -> str:
        return " ".join([card.utf8() for card in self.cards])
