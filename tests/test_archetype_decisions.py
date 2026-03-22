"""Tests for archetype player decision logic covering all branches."""

import unittest
from unittest.mock import Mock, patch

from maverick import Card, Suit, Rank, Holding
from maverick.enums import ActionType
from maverick.playerstate import PlayerState
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
)

def _make_bot(cls, stack=500):
    bot = cls(
        uid="test",
        name="Test"
    )
    return bot

def _make_game(pot=100, big_blind=10, community_cards=None, current_bet=20, n_players=3, stack=500):
    game = Mock()
    game.state.pot = pot
    game.state.big_blind = big_blind
    game.state.current_bet = current_bet
    game.state.community_cards = community_cards if community_cards is not None else []
    game.state.get_players_in_hand.return_value = [Mock() for _ in range(n_players)]
    game.rules.showdown.hole_cards_required = 0
    snapshot = Mock()
    snapshot.uid = "test"
    snapshot.state.stack = stack
    snapshot.state.current_bet = current_bet
    game.get_player_snapshot.return_value = snapshot
    return game

# ---------------------------------------------------------------------------
# ABCBot
# ---------------------------------------------------------------------------

class TestABCBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.80)
    def test_bets_with_strong_hand(self, _mock):
        bot = _make_bot(ABCBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.80)
    def test_raises_with_strong_hand_when_no_bet(self, _mock):
        bot = _make_bot(ABCBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.50)
    def test_calls_with_decent_hand_and_good_pot_odds(self, _mock):
        bot = _make_bot(ABCBot)
        # call_amount * 3 <= pot: 10 * 3 = 30 <= 100
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.50)
    def test_folds_with_decent_hand_but_bad_pot_odds(self, _mock):
        bot = _make_bot(ABCBot)
        # call_amount * 3 > pot: 50 * 3 = 150 > 100
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=50,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.30)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(ABCBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.30)
    def test_folds_as_fallback(self, _mock):
        bot = _make_bot(ABCBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.abc.estimate_holding_strength", return_value=0.80)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(ABCBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN), Card(suit=Suit.DIAMONDS, rank=Rank.FIVE)]
        game = _make_game(community_cards=community)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        # Verify community-cards path was taken (n_simulations=500)
        _mock.assert_called_once()
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 500)

# ---------------------------------------------------------------------------
# TightAggressiveBot
# ---------------------------------------------------------------------------

class TestTightAggressiveBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.70)
    def test_raises_with_strong_hand(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.70)
    def test_bets_with_strong_hand_when_no_raise(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.45)
    def test_calls_with_playable_hand_and_good_odds(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        # call_amount * 3 <= pot: 10 * 3 = 30 <= 100
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.30)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.30)
    def test_folds_as_fallback(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.tight_agressive.estimate_holding_strength", return_value=0.70)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(TightAggressiveBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 800)

# ---------------------------------------------------------------------------
# LooseAggressiveBot
# ---------------------------------------------------------------------------

class TestLooseAggressiveBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.40)
    def test_raises_with_any_equity(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.40)
    def test_bets_with_any_equity_when_no_raise(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.10)
    def test_calls_when_equity_too_low_to_raise(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.10)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.10)
    def test_folds_as_last_resort(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.loose_aggressive.estimate_holding_strength", return_value=0.40)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(LooseAggressiveBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 500)

# ---------------------------------------------------------------------------
# TightPassiveBot
# ---------------------------------------------------------------------------

class TestTightPassiveBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.tight_passive.estimate_holding_strength", return_value=0.80)
    def test_checks_when_available_despite_strong_hand(self, _mock):
        bot = _make_bot(TightPassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK, ActionType.BET],
            min_raise_amount=10,
            call_amount=0,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.tight_passive.estimate_holding_strength", return_value=0.80)
    def test_calls_with_strong_hand_and_tiny_amount(self, _mock):
        # call_amount <= stack * 0.1: 10 <= 500 * 0.1 = 50
        bot = _make_bot(TightPassiveBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.tight_passive.estimate_holding_strength", return_value=0.80)
    def test_folds_when_call_amount_too_large(self, _mock):
        # call_amount > stack * 0.1: 100 > 500 * 0.1 = 50
        bot = _make_bot(TightPassiveBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=100,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.tight_passive.estimate_holding_strength", return_value=0.30)
    def test_folds_with_weak_hand(self, _mock):
        bot = _make_bot(TightPassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.tight_passive.estimate_holding_strength", return_value=0.80)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(TightPassiveBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 400)

# ---------------------------------------------------------------------------
# LoosePassiveBot
# ---------------------------------------------------------------------------

class TestLoosePassiveBotDecisions(unittest.TestCase):

    def test_checks_when_available(self):
        bot = _make_bot(LoosePassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK, ActionType.BET],
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    def test_calls_when_no_check(self):
        bot = _make_bot(LoosePassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    def test_bets_when_only_option(self):
        bot = _make_bot(LoosePassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET],
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    def test_bets_amount_capped_at_stack(self):
        bot = _make_bot(LoosePassiveBot, stack=5)
        game = _make_game(stack=5)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET],
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        self.assertEqual(action.amount, 5)

    def test_folds_when_only_option(self):
        bot = _make_bot(LoosePassiveBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

# ---------------------------------------------------------------------------
# ManiacBot
# ---------------------------------------------------------------------------

class TestManiacBotDecisions(unittest.TestCase):

    def test_always_raises_when_available(self):
        bot = _make_bot(ManiacBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    def test_bets_when_no_raise(self):
        bot = _make_bot(ManiacBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    def test_goes_all_in_when_stack_small_relative_to_pot(self):
        # stack <= pot * 2: 50 <= 100 * 2 = 200 ✓
        bot = _make_bot(ManiacBot, stack=50)
        game = _make_game(pot=100, stack=50)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.ALL_IN, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.ALL_IN)

    def test_does_not_go_all_in_when_stack_too_large(self):
        # stack > pot * 2: 1000 > 100 * 2 = 200
        bot = _make_bot(ManiacBot, stack=1000)
        game = _make_game(pot=100, stack=1000)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.ALL_IN, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    def test_calls_when_cannot_raise_or_bet(self):
        bot = _make_bot(ManiacBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    def test_checks_when_available(self):
        bot = _make_bot(ManiacBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    def test_folds_as_last_resort(self):
        bot = _make_bot(ManiacBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

# ---------------------------------------------------------------------------
# BullyBot
# ---------------------------------------------------------------------------

class TestBullyBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.50)
    def test_raises_with_pressure_hand(self, _mock):
        bot = _make_bot(BullyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.70)
    def test_bets_with_strong_hand_when_no_raise(self, _mock):
        bot = _make_bot(BullyBot)
        game = _make_game(pot=50)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.70)
    def test_bets_uses_min_bet_when_pot_is_zero(self, _mock):
        # pot=0, so bet_amount = 0 < min_bet_amount, triggers fallback
        bot = _make_bot(BullyBot)
        game = _make_game(pot=0)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        self.assertGreater(action.amount, 0)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.50)
    def test_calls_when_amount_within_30_percent_stack(self, _mock):
        # call_amount <= stack * 0.3: 10 <= 500 * 0.3 = 150
        bot = _make_bot(BullyBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.50)
    def test_does_not_call_large_amounts(self, _mock):
        # call_amount > stack * 0.3: 200 > 500 * 0.3 = 150
        bot = _make_bot(BullyBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=200,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.20)
    def test_checks_when_hand_too_weak_to_raise(self, _mock):
        bot = _make_bot(BullyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.20)
    def test_folds_as_fallback(self, _mock):
        bot = _make_bot(BullyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.bully.estimate_holding_strength", return_value=0.70)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(BullyBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 400)

# ---------------------------------------------------------------------------
# GrinderBot
# ---------------------------------------------------------------------------

class TestGrinderBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.70)
    def test_raises_with_value_hand(self, _mock):
        bot = _make_bot(GrinderBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.70)
    def test_bets_with_value_hand_when_no_raise(self, _mock):
        bot = _make_bot(GrinderBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.50)
    def test_calls_with_profitable_hand_and_2to1_odds(self, _mock):
        # call_amount <= pot * 0.5: 10 <= 100 * 0.5 = 50
        bot = _make_bot(GrinderBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.50)
    def test_folds_with_marginal_odds(self, _mock):
        # call_amount > pot * 0.5: 60 > 100 * 0.5 = 50
        bot = _make_bot(GrinderBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=60,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.30)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(GrinderBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.30)
    def test_folds_as_fallback(self, _mock):
        bot = _make_bot(GrinderBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.grinder.estimate_holding_strength", return_value=0.70)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(GrinderBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 600)

# ---------------------------------------------------------------------------
# GTOBot
# ---------------------------------------------------------------------------

class TestGTOBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.80)
    def test_bets_with_strong_hand(self, _mock):
        bot = _make_bot(GTOBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.80)
    def test_raises_with_strong_hand_when_no_bet(self, _mock):
        bot = _make_bot(GTOBot)
        game = _make_game(pot=100, current_bet=20)
        game.get_player_snapshot.return_value.state.current_bet = 0
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=20,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.55)
    def test_calls_with_medium_hand_and_good_pot_odds(self, _mock):
        # call_amount <= pot: 50 <= 100
        bot = _make_bot(GTOBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=50,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.55)
    def test_folds_with_medium_hand_when_bet_too_large(self, _mock):
        # call_amount > pot: 150 > 100
        bot = _make_bot(GTOBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=150,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.30)
    def test_checks_balanced(self, _mock):
        bot = _make_bot(GTOBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.30)
    def test_folds_when_no_good_option(self, _mock):
        bot = _make_bot(GTOBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.gto.estimate_holding_strength", return_value=0.80)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(GTOBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 1000)

# ---------------------------------------------------------------------------
# SharkBot
# ---------------------------------------------------------------------------

class TestSharkBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_raises_with_strong_hand(self, _mock):
        bot = _make_bot(SharkBot)
        game = _make_game(pot=100, current_bet=20)
        game.get_player_snapshot.return_value.state.current_bet = 0
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            call_amount=20,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_value_bets_with_strong_hand(self, _mock):
        bot = _make_bot(SharkBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_value_bet_uses_min_bet_when_pot_too_small(self, _mock):
        bot = _make_bot(SharkBot)
        # pot=0 so bet_amount = 0 < min_bet_amount triggers fallback
        game = _make_game(pot=0)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        self.assertGreater(action.amount, 0)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.40)
    def test_bluff_bets_with_exploitable_hand(self, _mock):
        # not strong (> 0.55), but exploitable (> 0.35)
        bot = _make_bot(SharkBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_calls_with_strong_hand_and_good_odds(self, _mock):
        # call_amount <= pot * 0.66: 50 <= 100 * 0.66 = 66
        bot = _make_bot(SharkBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=50,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_does_not_call_with_bad_odds(self, _mock):
        # call_amount > pot * 0.66: 80 > 100 * 0.66 = 66
        bot = _make_bot(SharkBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=80,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.20)
    def test_checks_to_trap(self, _mock):
        bot = _make_bot(SharkBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.20)
    def test_folds_when_not_profitable(self, _mock):
        bot = _make_bot(SharkBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.shark.estimate_holding_strength", return_value=0.70)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(SharkBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 800)

# ---------------------------------------------------------------------------
# FishBot
# ---------------------------------------------------------------------------

class TestFishBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_calls_with_bad_odds_signature_move(self, _mock):
        # call_amount <= stack * 0.4: 50 <= 500 * 0.4 = 200
        bot = _make_bot(FishBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=50,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_does_not_call_when_too_expensive(self, _mock):
        # call_amount > stack * 0.4: 300 > 500 * 0.4 = 200
        bot = _make_bot(FishBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=300,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(FishBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_bets_occasionally(self, _mock):
        bot = _make_bot(FishBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_raises_rarely(self, _mock):
        bot = _make_bot(FishBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.10)
    def test_folds_when_equity_too_low_to_raise(self, _mock):
        # equity <= 0.15 threshold, so any_hand is False, won't raise
        bot = _make_bot(FishBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.fish.estimate_holding_strength", return_value=0.50)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(FishBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 100)

# ---------------------------------------------------------------------------
# HeroCallerBot
# ---------------------------------------------------------------------------

class TestHeroCallerBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_calls_large_bets_with_marginal_hand(self, _mock):
        # marginal_hand > 0.20, call_amount <= stack * 0.6: 200 <= 500 * 0.6 = 300
        bot = _make_bot(HeroCallerBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            call_amount=200,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_does_not_call_when_too_expensive(self, _mock):
        # call_amount > stack * 0.6: 400 > 500 * 0.6 = 300
        bot = _make_bot(HeroCallerBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=400,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.10)
    def test_does_not_call_with_very_weak_hand(self, _mock):
        # equity <= 0.20 threshold
        bot = _make_bot(HeroCallerBot, stack=500)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.CHECK],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_checks_when_available(self, _mock):
        bot = _make_bot(HeroCallerBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_bets_sometimes(self, _mock):
        bot = _make_bot(HeroCallerBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_raises_rarely(self, _mock):
        bot = _make_bot(HeroCallerBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.10)
    def test_folds_only_when_forced(self, _mock):
        bot = _make_bot(HeroCallerBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.hero_caller.estimate_holding_strength", return_value=0.30)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(HeroCallerBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 300)

# ---------------------------------------------------------------------------
# ScaredMoneyBot
# ---------------------------------------------------------------------------

class TestScaredMoneyBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_checks_whenever_possible(self, _mock):
        bot = _make_bot(ScaredMoneyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK, ActionType.BET],
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_calls_tiny_amounts_with_premium_hand(self, _mock):
        # call_amount <= big_blind (10) AND <= stack * 0.05 (500 * 0.05 = 25)
        bot = _make_bot(ScaredMoneyBot, stack=500)
        game = _make_game(big_blind=10)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            call_amount=5,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_does_not_call_above_big_blind(self, _mock):
        # call_amount > big_blind: 20 > 10
        bot = _make_bot(ScaredMoneyBot, stack=500)
        game = _make_game(big_blind=10)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            call_amount=20,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_bets_min_with_premium_hand(self, _mock):
        bot = _make_bot(ScaredMoneyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.FOLD],
            call_amount=0,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        self.assertEqual(action.amount, 10)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.50)
    def test_folds_without_premium_hand(self, _mock):
        bot = _make_bot(ScaredMoneyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            call_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_folds_to_any_significant_pressure(self, _mock):
        bot = _make_bot(ScaredMoneyBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            call_amount=50,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.scared_money.estimate_holding_strength", return_value=0.90)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(ScaredMoneyBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            call_amount=0,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 300)

# ---------------------------------------------------------------------------
# WhaleBot
# ---------------------------------------------------------------------------

class TestWhaleBotDecisions(unittest.TestCase):

    def test_always_raises_when_available(self):
        bot = _make_bot(WhaleBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    def test_bets_big_when_no_raise(self):
        bot = _make_bot(WhaleBot)
        game = _make_game(pot=100)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    def test_bet_uses_min_bet_fallback_when_pot_is_small(self):
        # pot=0, so bet_amount = 0 < min_bet_amount * 3
        bot = _make_bot(WhaleBot)
        game = _make_game(pot=0)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)
        self.assertGreater(action.amount, 0)

    def test_calls_everything(self):
        bot = _make_bot(WhaleBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    def test_goes_all_in_when_available(self):
        bot = _make_bot(WhaleBot, stack=50)
        game = _make_game(stack=50)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.ALL_IN],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.ALL_IN)

    def test_checks_if_must(self):
        bot = _make_bot(WhaleBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    def test_rarely_folds(self):
        bot = _make_bot(WhaleBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

# ---------------------------------------------------------------------------
# TiltedBot
# ---------------------------------------------------------------------------

class TestTiltedBotDecisions(unittest.TestCase):

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_goes_all_in_when_tilted_and_stack_small(self, _mock):
        # stack < pot * 2: 50 < 100 * 2 = 200, tilted_mindset = True (0.30 > 0.20)
        bot = _make_bot(TiltedBot, stack=50)
        game = _make_game(pot=100, stack=50)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.ALL_IN, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.ALL_IN)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.10)
    def test_does_not_go_all_in_when_equity_too_low(self, _mock):
        # tilted_mindset = False (0.10 <= 0.20)
        bot = _make_bot(TiltedBot, stack=50)
        game = _make_game(pot=100, stack=50)
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.ALL_IN, ActionType.RAISE],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_raises_aggressively(self, _mock):
        bot = _make_bot(TiltedBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.RAISE, ActionType.CALL],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.RAISE)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_bets_aggressively(self, _mock):
        bot = _make_bot(TiltedBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.BET, ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.BET)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_calls_too_often(self, _mock):
        bot = _make_bot(TiltedBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CALL, ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CALL)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_checks_when_nothing_else(self, _mock):
        bot = _make_bot(TiltedBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.CHECK)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_folds_as_last_resort(self, _mock):
        bot = _make_bot(TiltedBot)
        game = _make_game()
        action = bot.decide_action(
            game=game,
            valid_actions=[ActionType.FOLD],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        self.assertEqual(action.action_type, ActionType.FOLD)

    @patch("maverick.players.archetypes.tilted.estimate_holding_strength", return_value=0.30)
    def test_uses_community_cards_path(self, _mock):
        bot = _make_bot(TiltedBot)
        community = [Card(suit=Suit.CLUBS, rank=Rank.TEN)]
        game = _make_game(community_cards=community)
        bot.decide_action(
            game=game,
            valid_actions=[ActionType.CHECK],
            min_raise_amount=10,
            min_bet_amount=10,
        )
        call_kwargs = _mock.call_args
        self.assertEqual(call_kwargs.kwargs.get("n_simulations"), 100)

if __name__ == "__main__":
    unittest.main()
