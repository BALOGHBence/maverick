import unittest

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import Game, PlayerLike, PlayerState, GameState


class TestFirstButtonLogic(unittest.TestCase):
    """Test Game initialization."""

    def test_invalid_first_button_position_raises(self):
        """Test that invalid first button position raises ValueError."""
        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
        ]

        with self.assertRaises(ValueError):
            game = Game(
                small_blind=10, big_blind=20, max_hands=1, first_button_position=-1
            )
            for player in players:
                game.add_player(player)

        with self.assertRaises(ValueError):
            game = Game(
                small_blind=10, big_blind=20, max_hands=1, first_button_position="1"
            )
            for player in players:
                game.add_player(player)

    def test_first_button_position_random(self):
        """Test random first button position is within range on game initialization."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
        ]

        for player in players:
            game.add_player(player)

        self.assertLess(game._find_first_button_position(), len(players))


if __name__ == "__main__":
    unittest.main()
