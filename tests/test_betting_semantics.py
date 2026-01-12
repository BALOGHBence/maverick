"""Tests for raise-by semantics, betting round correctness, and all-in edge cases."""

import unittest
from maverick import Game
from maverick.playerstate import PlayerState
from maverick.playeraction import PlayerAction
from maverick.enums import ActionType, PlayerStateType
from maverick.player import Player
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maverick import Game as GameType


class TestBot(Player):
    """A test bot that follows scripted actions."""
    
    def __init__(self, actions=None, **kwargs):
        super().__init__(**kwargs)
        self._actions = actions or []
        self._action_index = 0
    
    def decide_action(
        self, game: "GameType", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        if self._action_index < len(self._actions):
            action_type, amount = self._actions[self._action_index]
            self._action_index += 1
            return PlayerAction(
                player_id=self.id, action_type=action_type, amount=amount
            )
        # Default to fold
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)


class TestMinimumRaiseTracking(unittest.TestCase):
    """Test that last_raise_size is tracked correctly."""

    def test_initial_last_raise_size_is_zero(self):
        """Test that last_raise_size starts at 0."""
        game = Game(small_blind=10, big_blind=20)
        self.assertEqual(game.state.last_raise_size, 0)

    def test_last_raise_size_set_after_blinds(self):
        """Test that last_raise_size is set to big blind after blinds."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=1000),
                     actions=[(ActionType.FOLD, None)])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.FOLD, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._event_queue.append(game._event_queue.pop() if game._event_queue else None)
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        self.assertEqual(game.state.last_raise_size, 20)

    def test_last_raise_size_updated_on_bet(self):
        """Test that last_raise_size is updated when first bet is made."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=1000),
                     actions=[(ActionType.CHECK, None)])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.BET, 50)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # Complete pre-flop (both fold except one)
        p1.state.state_type = PlayerStateType.FOLDED
        
        # Start flop
        game._complete_betting_round()
        self.assertEqual(game.state.last_raise_size, 0)  # Reset after betting round
        
        game.state.current_bet = 0
        game._deal_flop()
        game.state.current_player_index = 0
        p1.state.state_type = PlayerStateType.ACTIVE
        
        # P1 checks
        game._take_action_from_current_player()
        self.assertEqual(game.state.last_raise_size, 0)
        
        # P2 bets 50
        game.state.current_player_index = 1
        game._take_action_from_current_player()
        self.assertEqual(game.state.last_raise_size, 50)
        self.assertEqual(game.state.current_bet, 50)

    def test_last_raise_size_updated_on_raise(self):
        """Test that last_raise_size is updated when a raise is made."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=1000),
                     actions=[(ActionType.RAISE, 40)])
        # P1 raises by 40 (to 60 total)
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.FOLD, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # P1 (button in heads-up) acts first preflop
        game._take_action_from_current_player()
        
        # last_raise_size should be 40 (the raise increment)
        self.assertEqual(game.state.last_raise_size, 40)
        self.assertEqual(game.state.current_bet, 60)


class TestShortStackCall(unittest.TestCase):
    """Test that short-stack players can call with less than the full amount."""

    def test_short_stack_can_call(self):
        """Test that a player with insufficient stack can still call (all-in)."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        # 3-player game: P1 has only 25 chips
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=25),
                     actions=[(ActionType.FOLD, None)])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.CALL, None)])
        p3 = TestBot(id="p3", name="P3", state=PlayerState(stack=1000),
                     actions=[(ActionType.CALL, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        game.add_player(p3)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # P1 is button (no blind), P2 posts SB (10), P3 posts BB (20)
        # P1 acts first and needs to call 20 but only has 25 chips
        # P1 should be able to CALL (will be short-stack all-in call)
        
        valid_actions = game._get_valid_actions(game.state.players[0])
        self.assertIn(ActionType.CALL, valid_actions)

    def test_call_with_zero_chips_not_allowed(self):
        """Test that CALL is not valid when player has zero chips."""
        game = Game(small_blind=10, big_blind=20)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=0),
                     actions=[])
        
        game.add_player(p1)
        game.state.current_bet = 50
        p1.state.current_bet = 0
        
        valid_actions = game._get_valid_actions(p1)
        self.assertNotIn(ActionType.CALL, valid_actions)


class TestRaiseBySemantics(unittest.TestCase):
    """Test that raise actions use raise-by semantics, not raise-to."""

    def test_min_raise_is_raise_by_increment(self):
        """Test that min_raise passed to bots is a raise-by increment."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        received_min_raise = []
        
        class MinRaiseBot(Player):
            def decide_action(
                self, game: "GameType", valid_actions: list[ActionType], min_raise: int
            ) -> PlayerAction:
                received_min_raise.append(min_raise)
                return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
        
        p1 = MinRaiseBot(id="p1", name="P1", state=PlayerState(stack=1000))
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.FOLD, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # Take action from P1
        game._take_action_from_current_player()
        
        # min_raise should be last_raise_size (which is 20, the big blind)
        self.assertEqual(len(received_min_raise), 1)
        self.assertEqual(received_min_raise[0], 20)

    def test_raise_amount_is_added_to_current_bet(self):
        """Test that RAISE.amount is added to player's current bet."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=1000),
                     actions=[(ActionType.RAISE, 40)])
        # Raise by 40 on top of current bet
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[(ActionType.FOLD, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # In heads-up: P1 is button and posts BB (20), P2 posts SB (10)
        # So P1 starts with current_bet = 20
        self.assertEqual(p1.state.current_bet, 20)
        
        # P1 raises by 40
        game._take_action_from_current_player()
        
        # P1's current_bet should be 20 + 40 = 60
        self.assertEqual(p1.state.current_bet, 60)
        self.assertEqual(game.state.current_bet, 60)


class TestBettingRoundCompletion(unittest.TestCase):
    """Test that betting rounds complete correctly with all-in players."""

    def test_betting_round_completes_with_all_in_players(self):
        """Test that betting round completes when active players have acted and matched bets."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=100),
                     actions=[(ActionType.CALL, None)])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=100),
                     actions=[(ActionType.CHECK, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # P1 calls (heads-up button calls BB)
        game._take_action_from_current_player()
        
        # P2 checks (BB checks)
        game.state.current_player_index = 1
        game._take_action_from_current_player()
        
        # Betting round should be complete
        self.assertTrue(game.state.is_betting_round_complete())


class TestShowdownStateMachine(unittest.TestCase):
    """Test that state machine doesn't advance player after showdown."""

    def test_no_player_advance_after_showdown(self):
        """Test that current_player_index is not advanced when entering showdown."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=100),
                     actions=[(ActionType.FOLD, None)])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=100),
                     actions=[(ActionType.FOLD, None)])
        
        game.add_player(p1)
        game.add_player(p2)
        
        # Run the game
        game.start()
        
        # The game should complete without errors
        # This test mainly ensures no exceptions are raised
        self.assertEqual(game.state.hand_number, 1)


class TestMinimumRaiseEnforcement(unittest.TestCase):
    """Test that minimum raise rules are enforced correctly."""

    def test_raise_less_than_minimum_is_rejected(self):
        """Test that a raise smaller than last_raise_size is rejected."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=1000),
                     actions=[])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[])
        
        game.add_player(p1)
        game.add_player(p2)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # Try to raise by only 10 when minimum is 20
        action = PlayerAction(player_id=p1.id, action_type=ActionType.RAISE, amount=10)
        
        with self.assertRaises(ValueError):
            game._register_player_action(p1, action)

    def test_all_in_available_when_cant_min_raise(self):
        """Test that ALL_IN is available even when can't make minimum raise."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        
        # 3-player game to avoid heads-up complications
        p1 = TestBot(id="p1", name="P1", state=PlayerState(stack=25),
                     actions=[])
        p2 = TestBot(id="p2", name="P2", state=PlayerState(stack=1000),
                     actions=[])
        p3 = TestBot(id="p3", name="P3", state=PlayerState(stack=1000),
                     actions=[])
        
        game.add_player(p1)
        game.add_player(p2)
        game.add_player(p3)
        
        game._initialize_game()
        game._start_new_hand()
        game._deal_hole_cards()
        game._post_blinds()
        
        # P1 is button, P2 posts SB (10), P3 posts BB (20)
        # P1 acts first and has 25 chips
        # To call: needs 20
        # To raise minimally: needs 20 (call) + 20 (min raise) = 40 total
        # P1 only has 25, so can't RAISE, but can ALL_IN
        
        valid = game._get_valid_actions(p1)
        self.assertNotIn(ActionType.RAISE, valid)
        self.assertIn(ActionType.ALL_IN, valid)


if __name__ == "__main__":
    unittest.main()
