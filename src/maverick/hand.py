from typing import Tuple, Iterator, Optional
from itertools import combinations

from pydantic import BaseModel

from .card import Card
from .utils import score_hand
from .enums import HandType

__all__ = ["Hand"]


class Hand(BaseModel):
    """
    Private cards plus as many community cards as needed to complete the hand.

    Fields
    ------
    private_cards : list[Card]
        The private cards held by the player.
    community_cards : list[Card]
        The community cards on the table.

    Examples
    --------
    >>> from maverick import Hand, Card
    >>> hand = Hand(
    ...     private_cards=[Card(suit='S', rank=14), Card(suit='H', rank=13)],
    ...     community_cards=[Card(suit='D', rank=10), Card(suit='C', rank=11), Card(suit='H', rank=12)]
    ... )
    >>> hand.score()
    (HandType.STRAIGHT, 8.1234)  # Example output, actual value may vary

    >>> from maverick import Hand, Card, Deck
    >>> deck = Deck.standard_deck(shuffle=True)
    >>> private_cards = deck.deal(2)
    >>> community_cards = deck.deal(5)
    >>> hand = Hand(private_cards=private_cards, community_cards=community_cards)
    >>> hand.score()
    (HandType.FLUSH, 6.5678)  # Example output, actual value may vary
    """

    private_cards: list[Card]
    community_cards: list[Card]

    def score(self) -> Tuple[HandType, float]:
        """Classifies and scores the hand.

        Returns (HandType, float_score) where higher scores = stronger hands.
        """
        all_cards = self.private_cards + self.community_cards
        return score_hand(all_cards)

    @classmethod
    def all_possible_hands(
        cls, private_cards: list[Card], community_cards: Optional[list[Card]] = None
    ) -> Iterator["Hand"]:
        """Generate all possible hands."""
        if community_cards is None:
            for combination in combinations(private_cards, 5):
                combo = list(combination)
                yield cls(private_cards=combo[:2], community_cards=combo[2:])
        else:
            for combination in combinations(community_cards, 3):
                yield cls(
                    private_cards=private_cards, community_cards=list(combination)
                )

    def __repr__(self) -> str:
        private_cards = [card.utf8() for card in self.private_cards]
        community_cards = [card.utf8() for card in self.community_cards]
        return " ".join(private_cards + community_cards)
