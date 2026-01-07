from typing import Tuple

from .card import Card
from .enums import HandType

__all__ = ["score_hand"]


def _check_four_of_a_kind(numbers: list[str]) -> float:
    for i in numbers:
        if numbers.count(i) == 4:
            four = i
        elif numbers.count(i) == 1:
            card = i
    score = 105 + four + card / 100
    return score


def _check_full_house(numbers: list[str]) -> float:
    for i in numbers:
        if numbers.count(i) == 3:
            full = i
        elif numbers.count(i) == 2:
            p = i
    score = 90 + full + p / 100
    return score


def _check_three_of_a_kind(numbers: list[str]) -> float:
    cards = []
    for i in numbers:
        if numbers.count(i) == 3:
            three = i
        else:
            cards.append(i)
    score = 45 + three + max(cards) + min(cards) / 1000
    return score


def _check_two_pair(numbers: list[str]) -> float:
    pairs = []
    cards = []
    for i in numbers:
        if numbers.count(i) == 2:
            pairs.append(i)
        elif numbers.count(i) == 1:
            cards.append(i)
            cards = sorted(cards, reverse=True)
    score = 30 + max(pairs) + min(pairs) / 100 + cards[0] / 1000
    return score


def _check_pair(numbers: list[str]) -> float:
    pair = []
    cards = []
    for i in numbers:
        if numbers.count(i) == 2:
            pair.append(i)
        elif numbers.count(i) == 1:
            cards.append(i)
            cards = sorted(cards, reverse=True)
    score = 15 + pair[0] + cards[0] / 100 + cards[1] / 1000 + cards[2] / 10000
    return score


def score_hand(hand: list[Card]) -> Tuple[HandType, float]:
    """Classifies and scores a poker hand."""

    assert len(hand) == 5, "Hand must contain exactly 5 cards."

    # We get the suit for each card in the hand
    suit_values = [card.suit.value for card in hand]
    rank_values = [card.rank.value for card in hand]

    # We count repetitions for each number
    rnum = [rank_values.count(i) for i in rank_values]

    # We count repetitions for each letter
    rlet = [suit_values.count(i) for i in suit_values]

    # The difference between the greater and smaller number in the hand
    dif = max(rank_values) - min(rank_values)

    handtype = ""
    score = 0
    if 5 in rlet:
        if rank_values == [14, 13, 12, 11, 10]:
            handtype = HandType.ROYAL_FLUSH
            score = 135
        elif dif == 4 and max(rnum) == 1:
            handtype = HandType.STRAIGHT_FLUSH
            score = 120 + max(rank_values)
        elif 4 in rnum:
            handtype == HandType.FOUR_OF_A_KIND
            score = _check_four_of_a_kind(rank_values)
        elif sorted(rnum) == [2, 2, 3, 3, 3]:
            handtype == HandType.FULL_HOUSE
            score = _check_full_house(rank_values)
        elif 3 in rnum:
            handtype = HandType.THREE_OF_A_KIND
            score = _check_three_of_a_kind(rank_values)
        elif rnum.count(2) == 4:
            handtype = HandType.TWO_PAIR
            score = _check_two_pair(rank_values)
        elif rnum.count(2) == 2:
            handtype = HandType.PAIR
            score = _check_pair(rank_values)
        else:
            handtype = HandType.FLUSH
            score = 75 + max(rank_values) / 100
    elif 4 in rnum:
        handtype = HandType.FOUR_OF_A_KIND
        score = _check_four_of_a_kind(rank_values)
    elif sorted(rnum) == [2, 2, 3, 3, 3]:
        handtype = HandType.FULL_HOUSE
        score = _check_full_house(rank_values)
    elif 3 in rnum:
        handtype = HandType.THREE_OF_A_KIND
        score = _check_three_of_a_kind(rank_values)
    elif rnum.count(2) == 4:
        handtype = HandType.TWO_PAIR
        score = _check_two_pair(rank_values)
    elif rnum.count(2) == 2:
        handtype = HandType.PAIR
        score = _check_pair(rank_values)
    elif dif == 4:
        handtype = HandType.STRAIGHT
        score = 65 + max(rank_values)
    else:
        handtype = HandType.HIGH_CARD
        n = sorted(rank_values, reverse=True)
        score = n[0] + n[1] / 100 + n[2] / 1000 + n[3] / 10000 + n[4] / 100000

    return handtype, score
