from enum import Enum, auto

__all__ = [
    "Suit",
    "Rank",
    "Street",
    "HandType",
    "PlayerPosition",
    "PlayerState",
    "GameStateType",
    "ActionType",
    "GameEventType",
]


class Suit(Enum):
    """
    Card suit enumeration.

    Represents the four suits in a standard deck of playing cards.

    Attributes
    ----------
    HEARTS : str
        Hearts suit, represented by 'H'.
    SPADES : str
        Spades suit, represented by 'S'.
    CLUBS : str
        Clubs suit, represented by 'C'.
    DIAMONDS : str
        Diamonds suit, represented by 'D'.
    """

    HEARTS = "H"
    SPADES = "S"
    CLUBS = "C"
    DIAMONDS = "D"


class Rank(Enum):
    """
    Card rank enumeration.

    Represents the ranks of cards in a standard deck, with numeric values
    for comparison purposes. Ace is high (14).

    Attributes
    ----------
    TWO : int
        Rank value 2.
    THREE : int
        Rank value 3.
    FOUR : int
        Rank value 4.
    FIVE : int
        Rank value 5.
    SIX : int
        Rank value 6.
    SEVEN : int
        Rank value 7.
    EIGHT : int
        Rank value 8.
    NINE : int
        Rank value 9.
    TEN : int
        Rank value 10.
    JACK : int
        Rank value 11.
    QUEEN : int
        Rank value 12.
    KING : int
        Rank value 13.
    ACE : int
        Rank value 14 (high ace).
    """

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
    """
    Betting round enumeration for Texas Hold'em.

    Represents the different stages of a poker hand, ordered by when they occur.

    Attributes
    ----------
    PRE_FLOP : int
        First betting round, before any community cards are dealt (value 0).
    FLOP : int
        Second betting round, after three community cards are dealt (value 1).
    TURN : int
        Third betting round, after the fourth community card is dealt (value 2).
    RIVER : int
        Fourth betting round, after the fifth community card is dealt (value 3).
    SHOWDOWN : int
        Final stage where remaining players reveal their hands (value 4).
    """

    PRE_FLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


class HandType(Enum):
    """
    Poker hand type enumeration.

    Represents the different types of poker hands, from weakest to strongest.

    Attributes
    ----------
    HIGH_CARD : str
        Highest card wins, no pairs or better.
    PAIR : str
        Two cards of the same rank.
    TWO_PAIR : str
        Two different pairs.
    THREE_OF_A_KIND : str
        Three cards of the same rank.
    STRAIGHT : str
        Five cards in sequence, not all the same suit.
    FLUSH : str
        Five cards of the same suit, not in sequence.
    FULL_HOUSE : str
        Three of a kind plus a pair.
    FOUR_OF_A_KIND : str
        Four cards of the same rank.
    STRAIGHT_FLUSH : str
        Five cards in sequence, all of the same suit.
    ROYAL_FLUSH : str
        Ace, King, Queen, Jack, Ten, all of the same suit (best hand).
    """

    HIGH_CARD = auto()
    PAIR = auto()
    TWO_PAIR = auto()
    THREE_OF_A_KIND = auto()
    STRAIGHT = auto()
    FLUSH = auto()
    FULL_HOUSE = auto()
    FOUR_OF_A_KIND = auto()
    STRAIGHT_FLUSH = auto()
    ROYAL_FLUSH = auto()


class PlayerPosition(Enum):
    """
    Player position enumeration for Texas Hold'em.

    Positions determine the order of action and strategic advantage during a hand.
    Action generally proceeds clockwise, with players acting earlier having less
    information and players acting later having more information.

    Attributes
    ----------
    SMALL_BLIND : str
        The player immediately to the left of the button. Posts the small blind
        (a forced bet) before cards are dealt and acts early on all postflop streets.
    BIG_BLIND : str
        The player to the left of the small blind. Posts the big blind (a forced bet)
        before cards are dealt and acts early postflop, but last preflop.
    UNDER_THE_GUN : str
        The first player to act preflop after the blinds. Acts earliest among
        non-blind positions and therefore plays under the most informational disadvantage.
    MIDDLE_POSITION : str
        Any position between under-the-gun and the cutoff. Acts after early positions
        but before late positions, with moderate informational advantage.
    CUT_OFF : str
        The player immediately to the right of the button. A late position with
        significant informational advantage and wide opening opportunities.
    BUTTON : str
        The dealer position, marked by the dealer button. Acts last on all postflop
        streets and has the maximum informational advantage.
    """

    SMALL_BLIND = auto()
    BIG_BLIND = auto()
    UNDER_THE_GUN = auto()
    MIDDLE_POSITION = auto()
    CUT_OFF = auto()
    BUTTON = auto()


class PlayerState(Enum):
    """
    Player state enumeration.

    Represents the current state of a player during a poker hand.

    Attributes
    ----------
    ACTIVE : str
        Player is actively participating in the current hand and can take actions.
    FOLDED : str
        Player has folded and is no longer competing for the pot.
    ALL_IN : str
        Player has bet all their chips and cannot take further actions, but remains
        in the hand competing for pots they contributed to.
    """

    ACTIVE = auto()
    FOLDED = auto()
    ALL_IN = auto()


class GameStateType(Enum):
    """
    Game state enumeration for Texas Hold'em.

    Represents the different states of the game from waiting for players
    to game completion.

    Attributes
    ----------
    WAITING_FOR_PLAYERS : str
        Game is waiting for enough players to join.
    READY : str
        Enough players have joined; game is ready to start.
    DEALING : str
        Dealing hole cards to players and posting blinds.
    PRE_FLOP : str
        First betting round after hole cards are dealt.
    FLOP : str
        Second betting round after three community cards are dealt.
    TURN : str
        Third betting round after the fourth community card is dealt.
    RIVER : str
        Final betting round after the fifth community card is dealt.
    SHOWDOWN : str
        Players reveal hands and the winner is determined.
    HAND_COMPLETE : str
        Hand has ended; preparing for the next hand.
    GAME_OVER : str
        Game has ended (not enough players with chips).
    """

    WAITING_FOR_PLAYERS = auto()
    READY = auto()
    DEALING = auto()
    PRE_FLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    HAND_COMPLETE = auto()
    GAME_OVER = auto()


class ActionType(Enum):
    """
    Player action enumeration.

    Represents the different types of actions a player can take during a
    betting round.

    Attributes
    ----------
    FOLD : str
        Discard hand and forfeit any chance of winning the pot.
    CHECK : str
        Pass the action without betting (only valid when there's no bet to call).
    CALL : str
        Match the current bet to stay in the hand.
    BET : str
        Be the first to put chips into the pot in a betting round.
    RAISE : str
        Increase the current bet.
    ALL_IN : str
        Bet all remaining chips.
    """

    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class GameEventType(Enum):
    """
    Game event enumeration.

    Represents the different types of events that can occur during a poker game.

    Attributes
    ----------
    GAME_START : str
        Game begins.
    HAND_START : str
        New hand starts.
    HAND_END : str
        Hand ends.
    GAME_END : str
        Game ends.
    DEAL_HOLE_CARDS : str
        Hole cards dealt to players.
    DEAL_FLOP : str
        First three community cards dealt.
    DEAL_TURN : str
        Fourth community card dealt.
    DEAL_RIVER : str
        Fifth community card dealt.
    PLAYER_ACTION : str
        Player takes an action.
    BETTING_ROUND_COMPLETE : str
        Betting round completes.
    POST_BLINDS : str
        Blind bets posted.
    SHOWDOWN : str
        Showdown occurs.
    AWARD_POT : str
        Pot awarded to winner(s).
    """

    # Game lifecycle events
    GAME_START = auto()
    HAND_START = auto()
    HAND_END = auto()
    GAME_END = auto()

    # Dealing events
    DEAL_HOLE_CARDS = auto()
    DEAL_FLOP = auto()
    DEAL_TURN = auto()
    DEAL_RIVER = auto()

    # Player action events
    PLAYER_ACTION = auto()
    BETTING_ROUND_COMPLETE = auto()

    # Blind events
    POST_BLINDS = auto()

    # Showdown events
    SHOWDOWN = auto()
    AWARD_POT = auto()
