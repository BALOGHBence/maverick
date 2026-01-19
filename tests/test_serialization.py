import unittest

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import (
    Game,
    PlayerLike,
    PlayerState,
    GameState,
    Player,
    GameEvent,
    PlayerAction,
    ActionType,
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
        """Test PlayerState serialization and deserialization."""

        class CustomPlayer(Player):

            def __init__(self, event_counter=0, **kwargs):
                super().__init__(**kwargs)
                self._event_counter = event_counter

            @property
            def event_counter(self) -> int:
                return self._event_counter

            def on_event(self, event: GameEvent, game: Game) -> None:
                self._event_counter += 1

            def decide_action(
                self,
                *,
                game: Game,
                valid_actions: list["ActionType"],
                min_raise_amount: int,
                call_amount: int,
                **_,
            ) -> "PlayerAction":
                return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)

            def to_dict(self) -> dict:
                d = super().to_dict()
                d.update({"event_counter": self._event_counter})
                return d

        game = Game(small_blind=10, big_blind=20, max_hands=2)

        players: list[PlayerLike] = [
            CallBot(name="CallBot", state=PlayerState(stack=1000)),
            AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
            FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
            CustomPlayer(name="CustomBot", state=PlayerState(stack=1000)),
        ]

        for player in players:
            game.add_player(player)

        game.start()

        game_state = game.state.model_dump()
        recovered_game_state = GameState.model_validate(game_state)

        self.assertEqual(
            recovered_game_state.players[-1].event_counter,
            game.state.players[-1].event_counter,
        )


if __name__ == "__main__":
    unittest.main()
