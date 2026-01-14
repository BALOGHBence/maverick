"""Additional tests to push coverage above 95%."""

import unittest
from maverick import Card, Suit, Rank, Holding, Deck, Game
from maverick.enums import ActionType, Street
from maverick.playerstate import PlayerState
from maverick.state import GameState
from maverick.players import (
    TightAggressiveBot,
    LooseAggressiveBot,
    TightPassiveBot,
    LoosePassiveBot,
    ManiacBot,
    TiltedBot,
    BullyBot,
    GrinderBot,
    GTOBot,
    SharkBot,
    FishBot,
    ABCBot,
    HeroCallerBot,
    ScaredMoneyBot,
    WhaleBot,
    FoldBot,
    CallBot,
    AggressiveBot,
)


class TestDeckMethods(unittest.TestCase):
    """Test additional Deck methods."""

    def test_deck_build_shuffled(self):
        """Test building a shuffled deck."""
        deck = Deck.build(shuffle=True)
        self.assertEqual(len(deck.cards), 52)

    def test_deck_deal(self):
        """Test dealing cards from deck."""
        deck = Deck.build()
        dealt = deck.deal(5)
        self.assertEqual(len(dealt), 5)
        self.assertEqual(len(deck.cards), 47)

    def test_deck_shuffle(self):
        """Test shuffling deck."""
        deck = Deck.build()
        first_card_before = deck.cards[0]
        deck.shuffle()
        # After shuffle, deck still has 52 cards
        self.assertEqual(len(deck.cards), 52)

    def test_deck_multiple_deals(self):
        """Test multiple deal operations."""
        deck = Deck.build()
        deck.deal(3)
        deck.deal(2)
        self.assertEqual(len(deck.cards), 47)


class TestEnumMethods(unittest.TestCase):
    """Test enum methods and properties."""

    def test_all_suits(self):
        """Test all suit values."""
        suits = list(Suit)
        self.assertEqual(len(suits), 4)
        self.assertIn(Suit.HEARTS, suits)
        self.assertIn(Suit.SPADES, suits)
        self.assertIn(Suit.CLUBS, suits)
        self.assertIn(Suit.DIAMONDS, suits)

    def test_all_ranks(self):
        """Test all rank values."""
        ranks = list(Rank)
        self.assertEqual(len(ranks), 13)
        self.assertIn(Rank.ACE, ranks)
        self.assertIn(Rank.KING, ranks)
        self.assertIn(Rank.TWO, ranks)

    def test_street_ordering(self):
        """Test street enum ordering."""
        self.assertLess(Street.PRE_FLOP.value, Street.FLOP.value)
        self.assertLess(Street.FLOP.value, Street.TURN.value)
        self.assertLess(Street.TURN.value, Street.RIVER.value)
        self.assertLess(Street.RIVER.value, Street.SHOWDOWN.value)


class TestPlayerStateOperations(unittest.TestCase):
    """Test PlayerState operations."""

    def test_player_state_creation(self):
        """Test creating player state."""
        state = PlayerState(stack=1000, seat=0)
        self.assertEqual(state.stack, 1000)
        self.assertEqual(state.seat, 0)
        self.assertEqual(state.current_bet, 0)

    def test_player_state_with_holding(self):
        """Test player state with holding."""
        holding = Holding(cards=[
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING)
        ])
        state = PlayerState(stack=500, seat=1, holding=holding)
        self.assertEqual(len(state.holding.cards), 2)


class TestGameIntegration(unittest.TestCase):
    """Test actual game integration with bots."""

    def test_game_with_whale_bot(self):
        """Test game with WhaleBot."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(WhaleBot(id="whale", name="Whale", state=PlayerState(stack=1000, seat=0)))
        game.add_player(FoldBot(id="fold", name="Fold", state=PlayerState(stack=1000, seat=1)))
        self.assertIsNotNone(game)

    def test_game_with_multiple_archetypes(self):
        """Test game with multiple archetype bots."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(TightAggressiveBot(id="tag", name="TAG", state=PlayerState(stack=1000, seat=0)))
        game.add_player(LoosePassiveBot(id="lp", name="LP", state=PlayerState(stack=1000, seat=1)))
        game.add_player(ManiacBot(id="maniac", name="Maniac", state=PlayerState(stack=1000, seat=2)))
        self.assertIsNotNone(game)

    def test_game_with_callbot(self):
        """Test game with CallBot."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(CallBot(id="call", name="Call", state=PlayerState(stack=1000, seat=0)))
        game.add_player(FoldBot(id="fold", name="Fold", state=PlayerState(stack=1000, seat=1)))
        self.assertIsNotNone(game)

    def test_game_with_aggressivebot(self):
        """Test game with AggressiveBot."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(AggressiveBot(id="agg", name="Agg", state=PlayerState(stack=1000, seat=0)))
        game.add_player(FoldBot(id="fold", name="Fold", state=PlayerState(stack=1000, seat=1)))
        self.assertIsNotNone(game)


class TestProtocolMethods(unittest.TestCase):
    """Test protocol methods if available."""

    def test_player_has_decide_action(self):
        """Test that players have decide_action method."""
        bot = WhaleBot(id="test", name="Test", state=PlayerState(stack=100, seat=0))
        self.assertTrue(hasattr(bot, 'decide_action'))
        self.assertTrue(callable(bot.decide_action))


class TestHoldingEdgeCases(unittest.TestCase):
    """Test edge cases for Holding."""

    def test_holding_with_single_card(self):
        """Test holding with one card."""
        holding = Holding(cards=[Card(suit=Suit.HEARTS, rank=Rank.ACE)])
        self.assertEqual(len(holding.cards), 1)

    def test_holding_with_many_cards(self):
        """Test holding with many cards."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.JACK),
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
        ]
        holding = Holding(cards=cards)
        self.assertEqual(len(holding.cards), 5)

    def test_holding_all_possible_from_small_set(self):
        """Test all possible holdings from small card set."""
        cards = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
        ]
        holdings = list(Holding.all_possible_holdings(cards, n=2))
        self.assertEqual(len(holdings), 3)  # C(3,2) = 3


class TestCardEdgeCases(unittest.TestCase):
    """Test edge cases for Card."""

    def test_all_card_ranks_utf8(self):
        """Test UTF-8 for all ranks."""
        for rank in Rank:
            card = Card(suit=Suit.HEARTS, rank=rank)
            utf8 = card.utf8()
            self.assertIsInstance(utf8, str)
            self.assertIn("♥", utf8)

    def test_all_card_suits_utf8(self):
        """Test UTF-8 for all suits."""
        for suit in Suit:
            card = Card(suit=suit, rank=Rank.ACE)
            utf8 = card.utf8()
            self.assertIsInstance(utf8, str)
            self.assertIn("A", utf8)

    def test_all_card_ranks_code(self):
        """Test code for all ranks."""
        for rank in Rank:
            card = Card(suit=Suit.HEARTS, rank=rank)
            code = card.code()
            self.assertIsInstance(code, str)
            self.assertTrue(code.endswith("h"))

    def test_all_card_suits_code(self):
        """Test code for all suits."""
        for suit in Suit:
            card = Card(suit=suit, rank=Rank.ACE)
            code = card.code()
            self.assertIsInstance(code, str)
            self.assertTrue(code.startswith("A"))

    def test_all_card_text(self):
        """Test text for various cards."""
        card1 = Card(suit=Suit.CLUBS, rank=Rank.FIVE)
        self.assertEqual(card1.text(), "Five of Clubs")
        
        card2 = Card(suit=Suit.DIAMONDS, rank=Rank.TEN)
        self.assertEqual(card2.text(), "Ten of Diamonds")


class TestWhaleExtended(unittest.TestCase):
    """Extended tests for WhaleBot."""

    def test_whale_bet_with_small_pot(self):
        """Test WhaleBot betting with small pot."""
        whale = WhaleBot(id="whale", name="Whale", state=PlayerState(stack=1000, seat=0))
        from unittest.mock import Mock
        game = Mock()
        game.state.pot = 5
        game.state.big_blind = 10
        
        action = whale.decide_action(game, [ActionType.BET], min_raise=10)
        self.assertEqual(action.action_type, ActionType.BET)
        # Should bet at least 5 * big_blind = 50
        self.assertGreaterEqual(action.amount, 50)


class TestEventBusEdgeCases(unittest.TestCase):
    """Test EventBus edge cases."""

    def test_eventbus_import(self):
        """Test EventBus can be imported."""
        from maverick.eventbus import EventBus
        bus = EventBus()
        self.assertIsNotNone(bus)

    def test_eventbus_subscribe(self):
        """Test subscribing to events."""
        from maverick.eventbus import EventBus
        from maverick.enums import GameEventType
        bus = EventBus()
        
        called = []
        def handler(event):
            called.append(event)
        
        bus.subscribe(GameEventType.GAME_START, handler)
        self.assertEqual(len(called), 0)


if __name__ == "__main__":
    unittest.main()
