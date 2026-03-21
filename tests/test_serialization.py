import unittest

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import (
    Game,
    PlayerLike,
    PlayerState,
    GameState,
)


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

    def test_player_state_serialization(self):
        """Test PlayerSnapshot serialization and deserialization."""

        game = Game(small_blind=10, big_blind=20, max_hands=2)

        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
        ]

        for player in players:
            game.add_player(player)

        game.start()

        # Verify PlayerSnapshot round-trip: uid, name, and state should be preserved
        game_state = game.state.model_dump()
        recovered_game_state = GameState.model_validate(game_state)

        for orig, recovered in zip(game.state.players, recovered_game_state.players):
            self.assertEqual(orig.uid, recovered.uid)
            self.assertEqual(orig.name, recovered.name)
            self.assertEqual(orig.state.stack, recovered.state.stack)
            self.assertEqual(orig.state.state_type, recovered.state.state_type)


if __name__ == "__main__":
    unittest.main()
