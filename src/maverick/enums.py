from enum import Enum

__all__ = ["Suit", "Rank", "Street", "HandType", "PlayerPosition", "PlayerState"]


class Suit(Enum):
    HEARTS = "H"
    SPADES = "S"
    CLUBS = "C"
    DIAMONDS = "D"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Street(Enum):
    PRE_FLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


class HandType(Enum):
    HIGH_CARD = "high_card"
    PAIR = "pair"
    TWO_PAIR = "two_pair"
    THREE_OF_A_KIND = "three_of_a_kind"
    STRAIGHT = "straight"
    FLUSH = "flush"
    FULL_HOUSE = "full_house"
    FOUR_OF_A_KIND = "four_of_a_kind"
    STRAIGHT_FLUSH = "straight_flush"
    ROYAL_FLUSH = "royal_flush"


class PlayerPosition(Enum):
    """
    PlayerPosition represents a player's positional role at the poker table.

    Positions determine the order of action and strategic advantage during a hand.
    Action generally proceeds clockwise, with players acting earlier having less
    information and players acting later having more information.

    Positions:

    - SMALL_BLIND:
      The player immediately to the left of the button. Posts the small blind
      (a forced bet) before cards are dealt and acts early on all postflop streets.

    - BIG_BLIND:
      The player to the left of the small blind. Posts the big blind (a forced bet)
      before cards are dealt and acts early postflop, but last preflop.

    - UNDER_THE_GUN:
      The first player to act preflop after the blinds. Acts earliest among
      non-blind positions and therefore plays under the most informational disadvantage.

    - MIDDLE_POSITION:
      Any position between under-the-gun and the cutoff. Acts after early positions
      but before late positions, with moderate informational advantage.

    - CUT_OFF:
      The player immediately to the right of the button. A late position with
      significant informational advantage and wide opening opportunities.

    - BUTTON:
      The dealer position, marked by the dealer button. Acts last on all postflop
      streets and has the maximum informational advantage.
    """

    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"
    UNDER_THE_GUN = "under_the_gun"
    MIDDLE_POSITION = "middle_position"
    CUT_OFF = "cutoff"
    BUTTON = "button"


class PlayerState(Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
