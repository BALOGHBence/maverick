from typing import Tuple, Iterator, Optional
from itertools import combinations

from pydantic import BaseModel

from .card import Card
from .utils import score_hand
from .enums import HandType

__all__ = ["Hand"]


class Hand(BaseModel):
    """Private cards plus as many community cards as needed to complete the hand."""

    private_cards: list[Card]
    community_cards: list[Card]

    def score(self) -> Tuple[HandType, float]:
        """Classifies and scores the hand."""
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
