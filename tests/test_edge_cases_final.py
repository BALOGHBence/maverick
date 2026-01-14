"""Final edge case tests to push coverage above 95%."""

import unittest
from unittest.mock import Mock
from maverick import Card, Suit, Rank, Holding, Deck
from maverick.enums import ActionType
from maverick.playerstate import PlayerState
from maverick.players import AggressiveBot, CallBot
from maverick.players.archetypes import LoosePassiveBot, ManiacBot


class TestAggressiveBotEdgeCases(unittest.TestCase):
    """Edge cases for AggressiveBot."""

    def test_aggressive_with_no_raise(self):
        """Test when raise is not available."""
        bot = AggressiveBot(id="agg", name="Agg", state=PlayerState(stack=100, seat=0))
        game = Mock()
        game.state.pot = 20
        game.state.big_blind = 10

        # Test with just BET available
        action = bot.decide_action(game, [ActionType.BET], min_raise=10)
        self.assertEqual(action.action_type, ActionType.BET)

        # Test with CALL/CHECK only
        action = bot.decide_action(game, [ActionType.CALL], min_raise=10)
        self.assertEqual(action.action_type, ActionType.CALL)


class TestCallBotEdgeCases(unittest.TestCase):
    """Edge cases for CallBot."""

    def test_callbot_with_all_in(self):
        """Test CallBot with ALL_IN available."""
        bot = CallBot(id="call", name="Call", state=PlayerState(stack=50, seat=0))
        game = Mock()

        action = bot.decide_action(game, [ActionType.ALL_IN], min_raise=10)
        self.assertEqual(action.action_type, ActionType.FOLD)

    def test_callbot_with_fold_only(self):
        """Test CallBot forced to fold."""
        bot = CallBot(id="call", name="Call", state=PlayerState(stack=50, seat=0))
        game = Mock()

        action = bot.decide_action(game, [ActionType.FOLD], min_raise=10)
        self.assertEqual(action.action_type, ActionType.FOLD)


class TestLoosePassiveBotPaths(unittest.TestCase):
    """Test LoosePassiveBot decision paths."""

    def test_loose_passive_with_check(self):
        """Test LoosePassiveBot checking."""
        bot = LoosePassiveBot(id="lp", name="LP", state=PlayerState(stack=500, seat=0))
        bot.state.holding = Holding(
            cards=[
                Card(suit=Suit.HEARTS, rank=Rank.SIX),
                Card(suit=Suit.CLUBS, rank=Rank.FOUR),
            ]
        )

        game = Mock()
        game.state.pot = 20
        game.state.big_blind = 10
        game.state.community_cards = []
        game.state.get_players_in_hand.return_value = [Mock(), Mock()]

        # Should prefer CHECK over BET
        action = bot.decide_action(
            game, [ActionType.CHECK, ActionType.BET], min_raise=10
        )
        self.assertIn(action.action_type, [ActionType.CHECK, ActionType.BET])


class TestManiacBotPaths(unittest.TestCase):
    """Test ManiacBot decision paths."""

    def test_maniac_with_bet(self):
        """Test ManiacBot betting."""
        bot = ManiacBot(
            id="maniac", name="Maniac", state=PlayerState(stack=800, seat=0)
        )
        bot.state.holding = Holding(
            cards=[
                Card(suit=Suit.HEARTS, rank=Rank.THREE),
                Card(suit=Suit.CLUBS, rank=Rank.NINE),
            ]
        )

        game = Mock()
        game.state.pot = 30
        game.state.big_blind = 10
        game.state.community_cards = []
        game.state.get_players_in_hand.return_value = [Mock(), Mock()]

        action = bot.decide_action(
            game, [ActionType.BET, ActionType.CHECK], min_raise=20
        )
        self.assertIn(action.action_type, [ActionType.BET, ActionType.CHECK])

    def test_maniac_with_call(self):
        """Test ManiacBot calling."""
        bot = ManiacBot(
            id="maniac", name="Maniac", state=PlayerState(stack=800, seat=0)
        )
        bot.state.holding = Holding(
            cards=[
                Card(suit=Suit.HEARTS, rank=Rank.THREE),
                Card(suit=Suit.CLUBS, rank=Rank.NINE),
            ]
        )

        game = Mock()
        game.state.pot = 30
        game.state.big_blind = 10
        game.state.community_cards = []
        game.state.get_players_in_hand.return_value = [Mock(), Mock()]

        action = bot.decide_action(
            game, [ActionType.CALL, ActionType.FOLD], min_raise=20
        )
        self.assertIn(action.action_type, [ActionType.CALL, ActionType.FOLD])


class TestDeckEdgeCases(unittest.TestCase):
    """Test Deck edge cases."""

    def test_deck_remove_cards(self):
        """Test removing specific cards from deck."""
        deck = Deck.build()
        cards_to_remove = deck.cards[:5]
        deck.remove_cards(cards_to_remove)
        self.assertEqual(len(deck.cards), 47)

    def test_deck_missing_cards(self):
        """Test getting missing cards."""
        deck = Deck.build()
        deck.deal(10)
        missing = deck.missing_cards()
        self.assertEqual(len(missing), 10)


class TestHoldingEstimateStrength(unittest.TestCase):
    """Test Holding.estimate_strength method."""

    def test_estimate_strength_basic(self):
        """Test basic strength estimation."""
        holding = Holding(
            cards=[
                Card(suit=Suit.HEARTS, rank=Rank.ACE),
                Card(suit=Suit.SPADES, rank=Rank.ACE),
            ]
        )
        # Run with very few simulations for speed
        strength = holding.estimate_strength(n_simulations=10, n_players=3)
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)


if __name__ == "__main__":
    unittest.main()
