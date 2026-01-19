import unittest

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import Game, PlayerLike, PlayerState, GameState


class TestFirstButtonLogic(unittest.TestCase):
    """Test Game initialization."""

    def test_first_button_position_0(self):
        """Test game initialization with default parameters."""
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
