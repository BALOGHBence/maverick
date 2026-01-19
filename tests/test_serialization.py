import unittest

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import Game, PlayerLike, PlayerState, GameState


class TestGameStateSerialization(unittest.TestCase):
    """Test Game initialization."""

    def test_round_trip_via_dict(self):
        """Test game initialization with default parameters."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
        ]

        for player in players:
            game.add_player(player)

        game.start()

        payload = game.state.model_dump()
        payload_ = GameState.model_validate(payload).model_dump()
        self.assertEqual(payload, payload_)

    def test_round_trip_via_json(self):
        """Test game initialization with default parameters."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
        ]

        for player in players:
            game.add_player(player)

        game.start()

        payload = game.state.model_dump_json()
        payload_ = GameState.model_validate_json(payload).model_dump_json()
        self.assertEqual(payload, payload_)


if __name__ == "__main__":
    unittest.main()
