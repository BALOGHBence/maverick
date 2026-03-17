"""Tests for the game_id (unique game identifier) feature."""

import unittest

from maverick import Game, GameEvent, GameEventType, ActionType, Player, PlayerAction, PlayerState


class MockPlayer(Player):
    """A test bot that follows scripted actions."""

    def __init__(self, actions=None, **kwargs):
        super().__init__(**kwargs)
        self._actions = actions or []
        self._action_index = 0

    def decide_action(
        self,
        *,
        game,
        valid_actions,
        min_raise_amount,
        call_amount,
        min_bet_amount,
    ) -> PlayerAction:
        if self._action_index < len(self._actions):
            action_type, amount = self._actions[self._action_index]
            self._action_index += 1
            return PlayerAction(
                player_id=self.id,
                action_type=action_type,
                amount=amount if amount is not None else 0,
            )
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)


def _make_game(max_hands=1):
    """Helper to create a minimal two-player game."""
    game = Game(small_blind=1, big_blind=2, max_hands=max_hands)
    p1 = MockPlayer(
        id="p1",
        name="P1",
        state=PlayerState(stack=100),
        actions=[(ActionType.FOLD, None)],
    )
    p2 = MockPlayer(
        id="p2",
        name="P2",
        state=PlayerState(stack=100),
        actions=[(ActionType.FOLD, None)],
    )
    game.add_player(p1)
    game.add_player(p2)
    return game


class TestGameIdBeforeStart(unittest.TestCase):
    """Test game_id before the game has been started."""

    def test_game_id_is_none_before_start(self):
        """game_id should be None before start() is called."""
        game = Game(small_blind=1, big_blind=2)
        self.assertIsNone(game.game_id)


class TestGameIdAfterStart(unittest.TestCase):
    """Test game_id after the game has been started."""

    def test_game_id_is_string_after_start(self):
        """game_id should be a string after start() is called."""
        game = _make_game()
        game.start()
        self.assertIsInstance(game.game_id, str)

    def test_game_id_is_32_char_hex(self):
        """game_id should be a 32-character hexadecimal string."""
        game = _make_game()
        game.start()
        self.assertEqual(len(game.game_id), 32)
        # Should be a valid hex string
        int(game.game_id, 16)

    def test_game_id_is_set_when_game_started_event_fires(self):
        """game_id should be set by the time the GAME_STARTED handler is called."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        captured_game_id = []

        def on_game_started(event: GameEvent, g: Game):
            captured_game_id.append(g.game_id)

        game.subscribe(GameEventType.GAME_STARTED, on_game_started)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100),
            actions=[(ActionType.FOLD, None)],
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100),
            actions=[(ActionType.FOLD, None)],
        )
        game.add_player(p1)
        game.add_player(p2)
        game.start()

        self.assertEqual(len(captured_game_id), 1)
        self.assertIsNotNone(captured_game_id[0])
        self.assertEqual(len(captured_game_id[0]), 32)

    def test_game_id_is_read_only(self):
        """game_id property should be read-only."""
        game = _make_game()
        game.start()
        with self.assertRaises(AttributeError):
            game.game_id = "some-value"

    def test_game_id_unique_across_instances(self):
        """Different game instances started independently should have different game_ids."""
        game1 = _make_game()
        game2 = _make_game()
        game1.start()
        game2.start()
        self.assertNotEqual(game1.game_id, game2.game_id)


if __name__ == "__main__":
    unittest.main()
