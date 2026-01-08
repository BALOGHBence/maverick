from typing import Tuple, Iterator
from itertools import combinations

from pydantic import BaseModel

from .card import Card
from .scoring import score_hand
from .enums import HandType

__all__ = ["Hand"]


class Hand(BaseModel):
    """Private cards plus as many community cards as needed to complete the hand."""

    private_cards: list[Card]
    community_cards: list[Card]

    def score(self) -> Tuple[HandType, float]:
        """Classifies and scores the hand."""
        all_cards = self.private_cards + self.community_cards
        assert len(all_cards) == 5, "Exactly 5 cards are required to score a hand."
        # Placeholder for actual scoring logic
        return score_hand(all_cards)

    @classmethod
    def all_possible_hands(
        cls, private_cards: list[Card], community_cards: list[Card]
    ) -> Iterator["Hand"]:
        """Generate all possible hands."""
        for combination in combinations(community_cards, 3):
            yield cls(private_cards=private_cards, community_cards=list(combination))
