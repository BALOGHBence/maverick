"""Tests for the synchronous event dispatch system."""

import unittest
from typing import TYPE_CHECKING

from maverick import Game, GameEvent, GameEventType, ActionType
from maverick.player import Player
from maverick.playeraction import PlayerAction
from maverick.playerstate import PlayerState

if TYPE_CHECKING:
    from maverick import Game as GameType


class EventRecorder:
    """Helper class to record events in order."""

    def __init__(self):
        self.events = []

    def record(self, event: GameEvent):
        self.events.append(event)

    def clear(self):
        self.events = []

    def get_event_types(self):
        return [e.type for e in self.events]


class MockPlayer(Player):
    """A test bot that follows scripted actions."""

    def __init__(self, actions=None, **kwargs):
        super().__init__(**kwargs)
        self._actions = actions or []
        self._action_index = 0
        # Use object.__setattr__ to bypass Pydantic's validation for test attribute
        object.__setattr__(self, "observed_events", [])

    def decide_action(
        self, game: "GameType", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        if self._action_index < len(self._actions):
            action_type, amount = self._actions[self._action_index]
            self._action_index += 1
            return PlayerAction(player_id=self.id, action_type=action_type, amount=amount)
        # Default to fold
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)

    def on_event(self, event: GameEvent) -> None:
        """Record events for testing."""
        self.observed_events.append(event)


class TestGameEventModel(unittest.TestCase):
    """Test the GameEvent model properties."""

    def test_game_event_is_immutable(self):
        """Test that GameEvent is frozen and cannot be modified."""
        from maverick.enums import Street

        event = GameEvent(
            type=GameEventType.HAND_STARTED,
            hand_number=1,
            street=Street.PRE_FLOP,
            pot=0,
            current_bet=0,
        )

        with self.assertRaises(Exception):  # Pydantic raises ValidationError or similar
            event.pot = 100

    def test_game_event_forbids_extra_fields(self):
        """Test that GameEvent rejects extra fields."""
        from maverick.enums import Street

        with self.assertRaises(Exception):
            GameEvent(
                type=GameEventType.HAND_STARTED,
                hand_number=1,
                street=Street.PRE_FLOP,
                pot=0,
                current_bet=0,
                extra_field="should_fail",  # This should be rejected
            )


class TestEventSubscription(unittest.TestCase):
    """Test event subscription and handler registration."""

    def test_on_method_registers_handler(self):
        """Test that on() method registers a handler."""
        game = Game(small_blind=10, big_blind=20)
        recorder = EventRecorder()

        game.on(GameEventType.GAME_STARTED, recorder.record)

        # Verify handler is registered
        self.assertIn(GameEventType.GAME_STARTED, game._listeners)
        self.assertEqual(len(game._listeners[GameEventType.GAME_STARTED]), 1)

    def test_multiple_handlers_for_same_event(self):
        """Test that multiple handlers can be registered for the same event."""
        game = Game(small_blind=10, big_blind=20)
        recorder1 = EventRecorder()
        recorder2 = EventRecorder()

        game.on(GameEventType.GAME_STARTED, recorder1.record)
        game.on(GameEventType.GAME_STARTED, recorder2.record)

        self.assertEqual(len(game._listeners[GameEventType.GAME_STARTED]), 2)


class TestEventEmission(unittest.TestCase):
    """Test event emission at transition points."""

    def test_game_started_event_emitted(self):
        """Test that GAME_STARTED event is emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.on(GameEventType.GAME_STARTED, recorder.record)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        event_types = recorder.get_event_types()
        self.assertIn(GameEventType.GAME_STARTED, event_types)

    def test_hand_started_event_emitted(self):
        """Test that HAND_STARTED event is emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.on(GameEventType.HAND_STARTED, recorder.record)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        event_types = recorder.get_event_types()
        self.assertIn(GameEventType.HAND_STARTED, event_types)

    def test_player_action_event_emitted(self):
        """Test that PLAYER_ACTION events are emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.on(GameEventType.PLAYER_ACTION, recorder.record)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.CALL, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Should have at least one player action
        self.assertTrue(len(recorder.events) > 0)
        # Check that events contain player_id and action
        for event in recorder.events:
            self.assertIsNotNone(event.player_id)
            self.assertIsNotNone(event.action)

    def test_player_joined_event_emitted(self):
        """Test that PLAYER_JOINED event is emitted."""
        game = Game(small_blind=1, big_blind=2)
        recorder = EventRecorder()

        game.on(GameEventType.PLAYER_JOINED, recorder.record)

        p1 = MockPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        game.add_player(p1)

        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0].type, GameEventType.PLAYER_JOINED)
        self.assertEqual(recorder.events[0].player_id, "p1")

    def test_all_required_events_emitted(self):
        """Test that all required events are emitted during a complete hand."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        # Register for all event types
        for event_type in GameEventType:
            game.on(event_type, recorder.record)

        # Create players that will play through a hand
        p1 = MockPlayer(
            id="p1",
            name="P1",
            state=PlayerState(stack=100),
            actions=[
                (ActionType.CALL, None),  # Call BB
                (ActionType.CHECK, None),  # Check flop
                (ActionType.CHECK, None),  # Check turn
                (ActionType.CHECK, None),  # Check river
            ],
        )
        p2 = MockPlayer(
            id="p2",
            name="P2",
            state=PlayerState(stack=100),
            actions=[
                (ActionType.CHECK, None),  # Check after BB
                (ActionType.CHECK, None),  # Check flop
                (ActionType.CHECK, None),  # Check turn
                (ActionType.CHECK, None),  # Check river
            ],
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        event_types = recorder.get_event_types()

        # Check for required events
        required_events = [
            GameEventType.GAME_STARTED,
            GameEventType.HAND_STARTED,
            GameEventType.POST_BLINDS,
            GameEventType.PLAYER_ACTION,
            GameEventType.BETTING_ROUND_COMPLETED,
            GameEventType.DEAL_FLOP,
            GameEventType.DEAL_TURN,
            GameEventType.DEAL_RIVER,
            GameEventType.SHOWDOWN,
            GameEventType.HAND_ENDED,
        ]

        for required_event in required_events:
            self.assertIn(
                required_event, event_types, f"Event {required_event.name} was not emitted"
            )


class TestHandlerExecutionOrder(unittest.TestCase):
    """Test that handlers are called in registration order."""

    def test_handlers_called_in_registration_order(self):
        """Test that handlers are invoked in the order they were registered."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        call_order = []

        def handler1(event: GameEvent):
            call_order.append(1)

        def handler2(event: GameEvent):
            call_order.append(2)

        def handler3(event: GameEvent):
            call_order.append(3)

        game.on(GameEventType.GAME_STARTED, handler1)
        game.on(GameEventType.GAME_STARTED, handler2)
        game.on(GameEventType.GAME_STARTED, handler3)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Handlers should be called in registration order
        self.assertEqual(call_order, [1, 2, 3])


class TestHandlerExceptionSafety(unittest.TestCase):
    """Test that exceptions in handlers don't break the engine."""

    def test_exception_in_handler_does_not_crash_game(self):
        """Test that exceptions in handlers are caught and logged."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

        def failing_handler(event: GameEvent):
            raise ValueError("Test exception in handler")

        game.on(GameEventType.GAME_STARTED, failing_handler)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)

        # Should not raise an exception
        game.start()

        # Game should still complete
        self.assertEqual(game.state.hand_number, 1)

    def test_exception_in_one_handler_does_not_prevent_others(self):
        """Test that an exception in one handler doesn't prevent other handlers from running."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        successful_calls = []

        def failing_handler(event: GameEvent):
            raise ValueError("Test exception")

        def successful_handler(event: GameEvent):
            successful_calls.append(event)

        game.on(GameEventType.GAME_STARTED, failing_handler)
        game.on(GameEventType.GAME_STARTED, successful_handler)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Successful handler should still be called
        self.assertEqual(len(successful_calls), 1)


class TestNoHandlersBehavior(unittest.TestCase):
    """Test that engine behaves normally when no handlers are registered."""

    def test_game_runs_normally_without_handlers(self):
        """Test that game runs identically when no handlers are registered."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Game should complete normally
        self.assertEqual(game.state.hand_number, 1)


class TestPlayerEventHook(unittest.TestCase):
    """Test the optional player-level on_event hook."""

    def test_player_on_event_hook_called(self):
        """Test that player on_event hook is called for events."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Players should have observed events
        self.assertTrue(len(p1.observed_events) > 0)
        self.assertTrue(len(p2.observed_events) > 0)

    def test_player_hook_exception_does_not_crash_game(self):
        """Test that exceptions in player on_event hook are caught."""

        class FailingPlayer(MockPlayer):
            def on_event(self, event: GameEvent) -> None:
                raise ValueError("Test exception in player hook")

        game = Game(small_blind=1, big_blind=2, max_hands=1)

        p1 = FailingPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.FOLD, None)]
        )

        game.add_player(p1)
        game.add_player(p2)

        # Should not raise an exception
        game.start()

        # Game should still complete
        self.assertEqual(game.state.hand_number, 1)


class TestEventPayloadAccuracy(unittest.TestCase):
    """Test that event payloads reflect post-action state."""

    def test_player_action_event_reflects_post_action_state(self):
        """Test that PLAYER_ACTION events contain post-action state."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        action_events = []

        def record_action(event: GameEvent):
            if event.type == GameEventType.PLAYER_ACTION:
                action_events.append(event)

        game.on(GameEventType.PLAYER_ACTION, record_action)

        p1 = MockPlayer(
            id="p1", name="P1", state=PlayerState(stack=100), actions=[(ActionType.CALL, None)]
        )
        p2 = MockPlayer(
            id="p2", name="P2", state=PlayerState(stack=100), actions=[(ActionType.CHECK, None)]
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Check that action events have correct data
        self.assertTrue(len(action_events) > 0)
        for event in action_events:
            self.assertIsNotNone(event.player_id)
            self.assertIsNotNone(event.action)
            self.assertGreaterEqual(event.pot, 0)
            self.assertGreaterEqual(event.current_bet, 0)


if __name__ == "__main__":
    unittest.main()
