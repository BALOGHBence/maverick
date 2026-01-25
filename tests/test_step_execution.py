import unittest
from maverick import Game
from maverick.players import FoldBot, CallBot
from maverick.playerstate import PlayerState
from maverick.enums import GameStage, GameEventType


DEFAULT_SMALL_BLIND = 10
DEFAULT_BIG_BLIND = 20


def create_game(**kwargs) -> Game:
    base_kwargs = {
        "small_blind": DEFAULT_SMALL_BLIND,
        "big_blind": DEFAULT_BIG_BLIND,
    }
    base_kwargs.update(kwargs)
    return Game(**base_kwargs)


class TestStepExecution(unittest.TestCase):
    """Test step-by-step game execution."""

    def test_has_events_initially_false(self) -> None:
        """Test that has_events returns False when no events are queued."""
        game = create_game()
        self.assertFalse(game.has_events())

    def test_has_events_after_adding_event(self) -> None:
        """Test that has_events returns True when events are queued."""
        game = create_game()
        game._event_queue.append(GameEventType.GAME_STARTED)
        self.assertTrue(game.has_events())

    def test_step_returns_false_when_no_events(self) -> None:
        """Test that step returns False when queue is empty."""
        game = create_game()
        result = game.step()
        self.assertFalse(result)

    def test_step_processes_single_event(self) -> None:
        """Test that step processes exactly one event."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            FoldBot(id="p1", name="P1", state=PlayerState(stack=50, seat=0))
        )
        game.add_player(
            CallBot(id="p2", name="P2", state=PlayerState(stack=50, seat=1))
        )

        # Initialize game and add initial event
        game._initialize_game()
        game._event_queue.append(GameEventType.GAME_STARTED)

        # Verify we have events
        self.assertTrue(game.has_events())

        # Process one event (GAME_STARTED)
        result = game.step()
        self.assertTrue(result)

        # Game state should have changed to STARTED (and HAND_STARTED event queued)
        self.assertEqual(game.state.stage, GameStage.STARTED)
        self.assertTrue(game.has_events())  # Should have HAND_STARTED queued

        # Process next event (HAND_STARTED)
        result = game.step()
        self.assertTrue(result)

        # Now state should be DEALING
        self.assertEqual(game.state.stage, GameStage.DEALING)

    def test_step_by_step_execution_completes_game(self) -> None:
        """Test that stepping through all events completes a game."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            FoldBot(id="p1", name="P1", state=PlayerState(stack=50, seat=0))
        )
        game.add_player(
            CallBot(id="p2", name="P2", state=PlayerState(stack=50, seat=1))
        )

        # Initialize game and add initial event
        game._initialize_game()
        game._event_queue.append(GameEventType.GAME_STARTED)

        # Process all events one at a time
        event_count = 0
        while game.step():
            event_count += 1
            # Safety check to prevent infinite loops in test
            if event_count > 1000:
                self.fail("Processed too many events, possible infinite loop")

        # Game should have completed one hand
        self.assertEqual(game.state.hand_number, 1)
        self.assertFalse(game.has_events())

    def test_step_by_step_equivalent_to_start(self) -> None:
        """Test that step-by-step execution produces same result as start()."""
        # Game 1: using start()
        game1 = Game(small_blind=1, big_blind=2, max_hands=1)
        game1.add_player(
            FoldBot(id="p1", name="P1", state=PlayerState(stack=50, seat=0))
        )
        game1.add_player(
            CallBot(id="p2", name="P2", state=PlayerState(stack=50, seat=1))
        )
        game1.start()

        # Game 2: using step()
        game2 = Game(small_blind=1, big_blind=2, max_hands=1)
        game2.add_player(
            FoldBot(id="p1", name="P1", state=PlayerState(stack=50, seat=0))
        )
        game2.add_player(
            CallBot(id="p2", name="P2", state=PlayerState(stack=50, seat=1))
        )
        game2._initialize_game()
        game2._event_queue.append(GameEventType.GAME_STARTED)

        while game2.step():
            pass

        # Both games should have completed the same number of hands
        self.assertEqual(game1.state.hand_number, game2.state.hand_number)
        self.assertEqual(game1.state.hand_number, 1)

    def test_multiple_hands_with_step(self) -> None:
        """Test that step-by-step execution works for multiple hands."""
        game = Game(small_blind=1, big_blind=2, max_hands=2)
        game.add_player(
            FoldBot(id="p1", name="P1", state=PlayerState(stack=50, seat=0))
        )
        game.add_player(
            CallBot(id="p2", name="P2", state=PlayerState(stack=50, seat=1))
        )

        # Initialize and start
        game._initialize_game()
        game._event_queue.append(GameEventType.GAME_STARTED)

        # Process all events
        event_count = 0
        while game.step():
            event_count += 1
            if event_count > 2000:
                self.fail("Processed too many events")

        # Should have completed 2 hands
        self.assertEqual(game.state.hand_number, 2)


if __name__ == "__main__":
    unittest.main()
