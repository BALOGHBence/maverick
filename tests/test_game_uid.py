"""Tests for the game_id (unique game identifier) feature."""

import unittest

from maverick import Game, Player, PlayerState, PlayerAction, ActionType, GameEventType
from maverick.enums import GameStage
from maverick.players import FoldBot, CallBot


DEFAULT_SMALL_BLIND = 10
DEFAULT_BIG_BLIND = 20


def make_game(**kwargs) -> Game:
    base = {"small_blind": DEFAULT_SMALL_BLIND, "big_blind": DEFAULT_BIG_BLIND, "max_hands": 1}
    base.update(kwargs)
    return Game(**base)


def add_players(game: Game, n: int = 2) -> None:
    bots = [FoldBot, CallBot]
    for i in range(n):
        cls = bots[i % len(bots)]
        game.add_player(cls(name=f"Player{i}", state=PlayerState(stack=1000)))


class TestGameId(unittest.TestCase):
    """Tests for the game_id property."""

    def test_game_id_is_none_before_start(self):
        """game_id should be None before the game starts."""
        game = make_game()
        self.assertIsNone(game.game_id)

    def test_game_id_is_string_after_start(self):
        """game_id should be a string after the game starts."""
        game = make_game()
        add_players(game)
        game.start()
        self.assertIsInstance(game.game_id, str)

    def test_game_id_is_32_chars(self):
        """game_id should be a 32-character hex string (UUID4 hex)."""
        game = make_game()
        add_players(game)
        game.start()
        self.assertEqual(len(game.game_id), 32)

    def test_game_id_is_read_only(self):
        """game_id property should be read-only."""
        game = make_game()
        add_players(game)
        game.start()
        with self.assertRaises(AttributeError):
            game.game_id = "some-value"

    def test_game_id_unique_across_instances(self):
        """Two separate Game instances should have different game_ids."""
        game1 = make_game()
        game2 = make_game()
        add_players(game1)
        add_players(game2)
        game1.start()
        game2.start()
        self.assertNotEqual(game1.game_id, game2.game_id)

    def test_game_id_generated_on_game_started_event(self):
        """game_id should be set when the GAME_STARTED event is processed."""
        game = make_game(max_hands=5)
        add_players(game)
        game._initialize_game()
        game._event_queue.append(GameEventType.GAME_STARTED)

        # Before draining the GAME_STARTED event
        self.assertIsNone(game.game_id)

        game.step()  # process GAME_STARTED

        # After GAME_STARTED event is processed, game_id should be set
        self.assertIsNotNone(game.game_id)
        self.assertEqual(len(game.game_id), 32)


if __name__ == "__main__":
    unittest.main()
