from typing import Tuple

from ..card import Card
from ..enums import HandType

__all__ = ["score_hand"]


def _check_four_of_a_kind(numbers: list[int]) -> float:
    four_val = None
    kickers = []
    for i in numbers:
        if numbers.count(i) == 4:
            four_val = i
        else:
            kickers.append(i)
    kickers = sorted(set(kickers), reverse=True)
    score = 800 + four_val
    score += sum([kickers[i] / (100 ** (i + 1)) for i in range(len(kickers))])
    return score


def _check_full_house(numbers: list[int]) -> float:
    triple_val = None
    pair_val = None
    for i in numbers:
        if numbers.count(i) == 3:
            triple_val = i
        elif numbers.count(i) == 2:
            pair_val = i
    score = 700 + triple_val + pair_val / 100
    return score


def _check_three_of_a_kind(numbers: list[int]) -> float:
    triple_val = None
    kickers = []
    for i in numbers:
        if numbers.count(i) == 3:
            triple_val = i
        else:
            kickers.append(i)
    kickers = sorted(set(kickers), reverse=True)
    score = 400 + triple_val
    score += sum([kickers[i] / (100 ** (i + 1)) for i in range(len(kickers))])
    return score


def _check_two_pair(numbers: list[int]) -> float:
    pairs = []
    kickers = []
    for i in numbers:
        if numbers.count(i) == 2:
            pairs.append(i)
        elif numbers.count(i) == 1:
            kickers.append(i)
    pairs = sorted(set(pairs), reverse=True)
    kickers = sorted(set(kickers), reverse=True)
    score = 300 + pairs[0] + pairs[1] / 100
    score += sum([kickers[i] / (100 ** (i + 2)) for i in range(len(kickers))])
    return score


def _check_pair(numbers: list[int]) -> float:
    pair_val = None
    kickers = []
    for i in numbers:
        if numbers.count(i) == 2:
            pair_val = i
        else:
            kickers.append(i)
    kickers = sorted(set(kickers), reverse=True)
    score = 200 + pair_val
    score += sum([kickers[i] / (100 ** (i + 1)) for i in range(len(kickers))])
    return score


def score_hand(hand: list[Card]) -> Tuple[HandType, float]:
    """
    Classifies and scores a poker hand.

    Works with any number of cards (not just 5).
    Returns (HandType, float_score) where higher scores = stronger hands.

    Hand ranking (base scores):
    - High Card: 100+
    - Pair: 200+
    - Two Pair: 300+
    - Three of a Kind: 400+
    - Straight: 500+
    - Flush: 600+
    - Full House: 700+
    - Four of a Kind: 800+
    - Straight Flush: 900+
    - Royal Flush: 1000
    """

    assert len(hand) > 0, "At least one card is required to score a hand."

    # Extract suit and rank values
    suit_values = [card.suit.value for card in hand]
    rank_values = [card.rank.value for card in hand]

    # Count repetitions
    rnum = [rank_values.count(i) for i in rank_values]
    rlet = [suit_values.count(i) for i in suit_values]

    # Check for flush (all same suit, and at least 5 cards)
    is_flush = max(rlet) >= 5

    # Check for straight and find highest card in straight
    unique_ranks = sorted(set(rank_values))
    is_straight = False
    straight_high_card = 0

    if len(unique_ranks) >= 5:
        # Check if any 5 consecutive ranks exist
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i + 4] - unique_ranks[i] == 4:
                is_straight = True
                straight_high_card = unique_ranks[i + 4]

        # Special case: A-2-3-4-5 (wheel) - counts as 5-high, not ace-high
        if set([14, 2, 3, 4, 5]).issubset(set(unique_ranks)):
            is_straight = True
            if straight_high_card == 0:  # Only wheel, no higher straight
                straight_high_card = 5  # Wheel is 5-high

    handtype = HandType.HIGH_CARD
    score = 0.0

    # Royal Flush: A-K-Q-J-10 all same suit
    if (
        is_flush
        and is_straight
        and set([14, 13, 12, 11, 10]).issubset(set(rank_values))
    ):
        handtype = HandType.ROYAL_FLUSH
        score = 1000.0

    # Straight Flush
    elif is_flush and is_straight:
        handtype = HandType.STRAIGHT_FLUSH
        score = 900 + straight_high_card / 100

    # Four of a Kind
    elif 4 in rnum:
        handtype = HandType.FOUR_OF_A_KIND
        score = _check_four_of_a_kind(rank_values)

    # Full House
    elif 3 in rnum and 2 in rnum:
        handtype = HandType.FULL_HOUSE
        score = _check_full_house(rank_values)

    # Flush
    elif is_flush:
        handtype = HandType.FLUSH
        n = sorted(rank_values, reverse=True)
        score = 600 + sum([n[i] / (100 ** (i + 1)) for i in range(len(n))])

    # Straight
    elif is_straight:
        handtype = HandType.STRAIGHT
        score = 500 + straight_high_card / 100

    # Three of a Kind
    elif 3 in rnum:
        handtype = HandType.THREE_OF_A_KIND
        score = _check_three_of_a_kind(rank_values)

    # Two Pair
    elif rnum.count(2) >= 4:  # At least 2 pairs
        handtype = HandType.TWO_PAIR
        score = _check_two_pair(rank_values)

    # Pair
    elif 2 in rnum:
        handtype = HandType.PAIR
        score = _check_pair(rank_values)

    # High Card
    else:
        handtype = HandType.HIGH_CARD
        n = sorted(rank_values, reverse=True)
        score = 100 + sum([n[i] / (100 ** (i + 1)) for i in range(len(n))])

    return handtype, score
