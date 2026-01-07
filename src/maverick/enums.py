from enum import Enum

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

    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"
    UNDER_THE_GUN = "under_the_gun"
    MIDDLE_POSITION = "middle_position"
    CUT_OFF = "cutoff"
    BUTTON = "button"


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

    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"


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

    WAITING_FOR_PLAYERS = "waiting_for_players"
    READY = "ready"
    DEALING = "dealing"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    HAND_COMPLETE = "hand_complete"
    GAME_OVER = "game_over"


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

    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


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
    GAME_START = "game_start"
    HAND_START = "hand_start"
    HAND_END = "hand_end"
    GAME_END = "game_end"

    # Dealing events
    DEAL_HOLE_CARDS = "deal_hole_cards"
    DEAL_FLOP = "deal_flop"
    DEAL_TURN = "deal_turn"
    DEAL_RIVER = "deal_river"

    # Player action events
    PLAYER_ACTION = "player_action"
    BETTING_ROUND_COMPLETE = "betting_round_complete"

    # Blind events
    POST_BLINDS = "post_blinds"

    # Showdown events
    SHOWDOWN = "showdown"
    AWARD_POT = "award_pot"
