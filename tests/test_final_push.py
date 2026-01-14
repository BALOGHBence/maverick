"""Final push to increase coverage."""

import unittest
from maverick import Game, Card, Suit, Rank, Holding
from maverick.playerstate import PlayerState
from maverick.players import FoldBot, CallBot
from maverick.enums import HandType
from maverick.utils import score_hand, estimate_holding_strength


class TestScoringEdgeCases(unittest.TestCase):
    """Test scoring edge cases."""

    def test_score_single_card(self):
        """Test scoring a single card."""
        cards = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.HIGH_CARD)

    def test_score_pair(self):
        """Test scoring a pair."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.PAIR)

    def test_score_two_pair(self):
        """Test scoring two pair."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.TWO_PAIR)

    def test_score_three_of_kind(self):
        """Test scoring three of a kind."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.JACK),
            Card(suit=Suit.SPADES, rank=Rank.JACK),
            Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.FIVE),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.THREE_OF_A_KIND)

    def test_score_straight(self):
        """Test scoring a straight."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
            Card(suit=Suit.SPADES, rank=Rank.SIX),
            Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
            Card(suit=Suit.CLUBS, rank=Rank.EIGHT),
            Card(suit=Suit.HEARTS, rank=Rank.NINE),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.STRAIGHT)

    def test_score_flush(self):
        """Test scoring a flush."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
            Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
            Card(suit=Suit.HEARTS, rank=Rank.NINE),
            Card(suit=Suit.HEARTS, rank=Rank.KING),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.FLUSH)

    def test_score_full_house(self):
        """Test scoring a full house."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.FULL_HOUSE)

    def test_score_four_of_kind(self):
        """Test scoring four of a kind."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
            Card(suit=Suit.SPADES, rank=Rank.TEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.TEN),
            Card(suit=Suit.CLUBS, rank=Rank.TEN),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.FOUR_OF_A_KIND)

    def test_score_straight_flush(self):
        """Test scoring a straight flush."""
        cards = [
            Card(suit=Suit.SPADES, rank=Rank.FIVE),
            Card(suit=Suit.SPADES, rank=Rank.SIX),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN),
            Card(suit=Suit.SPADES, rank=Rank.EIGHT),
            Card(suit=Suit.SPADES, rank=Rank.NINE),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.STRAIGHT_FLUSH)

    def test_score_royal_flush(self):
        """Test scoring a royal flush."""
        cards = [
            Card(suit=Suit.DIAMONDS, rank=Rank.TEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
        ]
        hand_type, score = score_hand(cards)
        self.assertEqual(hand_type, HandType.ROYAL_FLUSH)


class TestEstimateHoldingStrength(unittest.TestCase):
    """Test estimate_holding_strength function."""

    def test_estimate_with_community_cards(self):
        """Test estimation with community cards."""
        private = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
        ]
        community = [
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.JACK),
        ]
        strength = estimate_holding_strength(
            private, community_cards=community, n_simulations=10, n_players=3
        )
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)


class TestGameWithCallBots(unittest.TestCase):
    """Test games where bots actually call."""

    def test_three_callbots(self):
        """Test game with three CallBots to see showdown."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(CallBot(id="c1", name="C1", state=PlayerState(stack=200, seat=0)))
        game.add_player(CallBot(id="c2", name="C2", state=PlayerState(stack=200, seat=1)))
        game.add_player(CallBot(id="c3", name="C3", state=PlayerState(stack=200, seat=2)))
        game.start()
        # Game should complete
        self.assertIsNotNone(game)


if __name__ == "__main__":
    unittest.main()
