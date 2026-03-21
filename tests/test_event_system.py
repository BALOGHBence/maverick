"""Tests for the synchronous event dispatch system."""

import unittest
from typing import TYPE_CHECKING

from maverick import (
    Game,
    GameEvent,
    GameEventType,
    ActionType,
    Player,
    PlayerAction,
    PlayerState,
)

if TYPE_CHECKING:
    from maverick import Game as GameType


class EventRecorder:
    """Helper class to record events in order."""

    def __init__(self):
        self.events = []

    def record(self, event: GameEvent, game: Game):
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
        self,
        *,
        game: "GameType",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        if self._action_index < len(self._actions):
            action_type, amount = self._actions[self._action_index]
            self._action_index += 1
            return PlayerAction(
                player_id=self.id,
                action_type=action_type,
                amount=amount if amount is not None else 0,
            )
        # Default to fold
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)

    def on_event(self, event: GameEvent, game: Game) -> None:
        """Record events for testing."""
        self.observed_events.append(event)

    def on_game_started(self, event: GameEvent, game: Game) -> None:
        pass


class TestGameEventModel(unittest.TestCase):
    """Test the GameEvent model properties."""

    def test_game_event_is_immutable(self):
        """Test that GameEvent is frozen and cannot be modified."""
        from maverick.enums import Street

        event = GameEvent(
            type=GameEventType.HAND_STARTED,
            hand_number=1,
            street=Street.PRE_FLOP,
        )

        with self.assertRaises(Exception):  # Pydantic raises ValidationError or similar
            event.hand_number = 100

    def test_game_event_forbids_extra_fields(self):
        """Test that GameEvent rejects extra fields."""
        from maverick.enums import Street

        with self.assertRaises(Exception):
            GameEvent(
                type=GameEventType.HAND_STARTED,
                hand_number=1,
                street=Street.PRE_FLOP,
                extra_field="should_fail",  # This should be rejected
            )


class TestEventSubscription(unittest.TestCase):
    """Test event subscription and handler registration."""

    def test_subscribe_method_registers_handler(self):
        """Test that subscribe() method registers a handler."""
        game = Game(small_blind=10, big_blind=20)
        recorder = EventRecorder()

        token = game.subscribe(GameEventType.GAME_STARTED, recorder.record)

        # Verify token is returned
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_multiple_handlers_for_same_event(self):
        """Test that multiple handlers can be registered for the same event."""
        game = Game(small_blind=10, big_blind=20)
        recorder1 = EventRecorder()
        recorder2 = EventRecorder()

        token1 = game.subscribe(GameEventType.GAME_STARTED, recorder1.record)
        token2 = game.subscribe(GameEventType.GAME_STARTED, recorder2.record)

        # Verify both tokens are different
        self.assertNotEqual(token1, token2)

    def test_unsubscribe_removes_handler(self):
        """Test that unsubscribe() removes a handler."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        token = game.subscribe(GameEventType.GAME_STARTED, recorder.record)
        game.unsubscribe(token)

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
        game.start()

        # Handler should not have been called
        self.assertEqual(len(recorder.events), 0)


class TestEventEmission(unittest.TestCase):
    """Test event emission at transition points."""

    def test_game_started_event_emitted(self):
        """Test that GAME_STARTED event is emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.subscribe(GameEventType.GAME_STARTED, recorder.record)

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
        game.start()

        event_types = recorder.get_event_types()
        self.assertIn(GameEventType.GAME_STARTED, event_types)

    def test_hand_started_event_emitted(self):
        """Test that HAND_STARTED event is emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.subscribe(GameEventType.HAND_STARTED, recorder.record)

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
        game.start()

        event_types = recorder.get_event_types()
        self.assertIn(GameEventType.HAND_STARTED, event_types)

    def test_player_action_event_emitted(self):
        """Test that PLAYER_ACTION_TAKEN events are emitted."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        recorder = EventRecorder()

        game.subscribe(GameEventType.PLAYER_ACTION_TAKEN, recorder.record)

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
            actions=[(ActionType.CALL, None)],
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

        game.subscribe(GameEventType.PLAYER_JOINED, recorder.record)

        p1 = MockPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        game.add_player(p1)

        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0].type, GameEventType.PLAYER_JOINED)
        self.assertEqual(recorder.events[0].player_id, "p1")

    def test_all_required_events_emitted(self):
        """Test that all required events are emitted during a complete hand."""
        game = Game(small_blind=1, big_blind=2, max_hands=1, first_button_position=0)
        recorder = EventRecorder()

        # Register for all event types
        for event_type in GameEventType:
            game.subscribe(event_type, recorder.record)

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
            GameEventType.BLINDS_POSTED,
            GameEventType.PLAYER_ACTION_TAKEN,
            GameEventType.BETTING_ROUND_COMPLETED,
            GameEventType.FLOP_DEALT,
            GameEventType.TURN_DEALT,
            GameEventType.RIVER_DEALT,
            GameEventType.SHOWDOWN_COMPLETED,
            GameEventType.HAND_ENDED,
        ]

        for required_event in required_events:
            self.assertIn(
                required_event,
                event_types,
                f"Event {required_event.name} was not emitted",
            )


class TestHandlerExecutionOrder(unittest.TestCase):
    """Test that handlers are called in registration order."""

    def test_handlers_called_in_registration_order(self):
        """Test that handlers are invoked in the order they were registered."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        call_order = []

        def handler1(event: GameEvent, game: Game):
            call_order.append(1)

        def handler2(event: GameEvent, game: Game):
            call_order.append(2)

        def handler3(event: GameEvent, game: Game):
            call_order.append(3)

        game.subscribe(GameEventType.GAME_STARTED, handler1)
        game.subscribe(GameEventType.GAME_STARTED, handler2)
        game.subscribe(GameEventType.GAME_STARTED, handler3)

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
        game.start()

        # Handlers should be called in registration order
        self.assertEqual(call_order, [1, 2, 3])


class TestHandlerExceptionSafety(unittest.TestCase):
    """Test that exceptions in handlers don't break the engine."""

    def test_exception_in_handler_does_not_crash_game(self):
        """Test that exceptions in handlers are caught and logged."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

        def failing_handler(event: GameEvent, game: Game):
            raise ValueError("Test exception in handler")

        game.subscribe(GameEventType.GAME_STARTED, failing_handler)

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

        # Should not raise an exception
        game.start()

        # Game should still complete
        self.assertEqual(game.state.hand_number, 1)

    def test_exception_in_one_handler_does_not_prevent_others(self):
        """Test that an exception in one handler doesn't prevent other handlers from running."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        successful_calls = []

        def failing_handler(event: GameEvent, game: Game):
            raise ValueError("Test exception")

        def successful_handler(event: GameEvent, game: Game):
            successful_calls.append(event)

        game.subscribe(GameEventType.GAME_STARTED, failing_handler)
        game.subscribe(GameEventType.GAME_STARTED, successful_handler)

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
        game.start()

        # Successful handler should still be called
        self.assertEqual(len(successful_calls), 1)


class TestNoHandlersBehavior(unittest.TestCase):
    """Test that engine behaves normally when no handlers are registered."""

    def test_game_runs_normally_without_handlers(self):
        """Test that game runs identically when no handlers are registered."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

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
        game.start()

        # Game should complete normally
        self.assertEqual(game.state.hand_number, 1)


class TestPlayerEventHook(unittest.TestCase):
    """Test the optional player-level on_event hook."""

    def test_player_on_event_hook_called(self):
        """Test that player on_event hook is called for events."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)

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
        game.start()

        # Players should have observed events
        self.assertTrue(len(p1.observed_events) > 0)
        self.assertTrue(len(p2.observed_events) > 0)

    def test_player_hook_exception_does_not_crash_game(self):
        """Test that exceptions in player on_event hook are caught."""

        class FailingPlayer(MockPlayer):
            def on_event(self, event: GameEvent, game: Game) -> None:
                raise ValueError("Test exception in player hook")

        game = Game(small_blind=1, big_blind=2, max_hands=1)

        p1 = FailingPlayer(
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

        # Should not raise an exception
        game.start()

        # Game should still complete
        self.assertEqual(game.state.hand_number, 1)


class TestEventPayloadAccuracy(unittest.TestCase):
    """Test that event payloads reflect post-action state."""

    def test_player_action_event_reflects_post_action_state(self):
        """Test that PLAYER_ACTION_TAKEN events contain post-action state."""
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        action_events = []

        def record_action(event: GameEvent, game: Game):
            if event.type == GameEventType.PLAYER_ACTION_TAKEN:
                action_events.append(event)

        game.subscribe(GameEventType.PLAYER_ACTION_TAKEN, record_action)

        p1 = MockPlayer(
            id="p1",
            name="P1",
            state=PlayerState(stack=100),
            actions=[(ActionType.CALL, None)],
        )
        p2 = MockPlayer(
            id="p2",
            name="P2",
            state=PlayerState(stack=100),
            actions=[(ActionType.CHECK, None)],
        )

        game.add_player(p1)
        game.add_player(p2)
        game.start()

        # Check that action events have correct data
        self.assertTrue(len(action_events) > 0)
        for event in action_events:
            self.assertIsNotNone(event.player_id)
            self.assertIsNotNone(event.action)


class TestEventBusHasSubscribers(unittest.TestCase):
    """Tests for EventBus.has_subscribers."""

    def _make_bus(self):
        from maverick.eventbus import EventBus

        return EventBus()

    def test_returns_false_when_no_subscribers(self):
        bus = self._make_bus()
        self.assertFalse(bus.has_subscribers(GameEventType.GAME_STATE_CHANGED))

    def test_returns_true_after_subscribing(self):
        bus = self._make_bus()
        bus.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: None)
        self.assertTrue(bus.has_subscribers(GameEventType.GAME_STATE_CHANGED))

    def test_returns_false_after_unsubscribing(self):
        bus = self._make_bus()
        token = bus.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: None)
        bus.unsubscribe(token)
        self.assertFalse(bus.has_subscribers(GameEventType.GAME_STATE_CHANGED))

    def test_only_matches_given_event_type(self):
        bus = self._make_bus()
        bus.subscribe(GameEventType.HAND_STARTED, lambda e, g: None)
        self.assertFalse(bus.has_subscribers(GameEventType.GAME_STATE_CHANGED))
        self.assertTrue(bus.has_subscribers(GameEventType.HAND_STARTED))


class TestGameStateChangedOptimization(unittest.TestCase):
    """Tests for the lazy serialization optimization in _update_state."""

    def _make_game(self):
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        p1 = MockPlayer(
            id="p1",
            name="P1",
            state=PlayerState(stack=500),
            actions=[(ActionType.FOLD, None)],
        )
        p2 = MockPlayer(
            id="p2",
            name="P2",
            state=PlayerState(stack=500),
            actions=[(ActionType.FOLD, None)],
        )
        game.add_player(p1)
        game.add_player(p2)
        return game

    def test_no_event_emitted_without_subscribers(self):
        game = self._make_game()
        events = []
        # Subscribe to ALL events and filter for GAME_STATE_CHANGED manually
        game.subscribe(GameEventType.HAND_STARTED, lambda e, g: None)  # unrelated sub
        original_emit = game._emit

        def capture(event):
            if event.type == GameEventType.GAME_STATE_CHANGED:
                events.append(event)
            original_emit(event)

        game._emit = capture
        game.start()
        self.assertEqual(len(events), 0)

    def test_event_emitted_with_correct_payload_when_subscriber_exists(self):
        game = self._make_game()
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        self.assertGreater(len(events), 0)
        for event in events:
            self.assertIn("before", event.payload)
            self.assertIn("after", event.payload)
            self.assertIsInstance(event.payload["before"], dict)
            self.assertIsInstance(event.payload["after"], dict)


class TestPlayerStateChangedEvents(unittest.TestCase):
    """Test that GAME_STATE_CHANGED is emitted for player-level state changes."""

    def _make_game_with_players(self, p1_actions, p2_actions, stacks=(500, 500)):
        game = Game(small_blind=10, big_blind=20, max_hands=1, first_button_position=0)
        p1 = MockPlayer(
            id="p1",
            name="P1",
            state=PlayerState(stack=stacks[0]),
            actions=p1_actions,
        )
        p2 = MockPlayer(
            id="p2",
            name="P2",
            state=PlayerState(stack=stacks[1]),
            actions=p2_actions,
        )
        game.add_player(p1)
        game.add_player(p2)
        return game, p1, p2

    def test_game_state_changed_emitted_when_player_folds(self):
        """GAME_STATE_CHANGED must be emitted when a player folds."""
        game, p1, p2 = self._make_game_with_players(
            p1_actions=[(ActionType.FOLD, None)],
            p2_actions=[],
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        # state_type is serialized as its integer value; FOLDED = 2
        FOLDED_VALUE = 2

        def _has_folded_player(payload):
            for player_data in payload.get("after", {}).get("players", []):
                if player_data.get("state", {}).get("state_type") == FOLDED_VALUE:
                    return True
            return False

        self.assertTrue(
            any(_has_folded_player(e.payload) for e in events),
            "No GAME_STATE_CHANGED event captured the fold transition",
        )

    def test_game_state_changed_emitted_when_player_goes_all_in(self):
        """GAME_STATE_CHANGED must be emitted when a player goes all-in."""
        game, p1, p2 = self._make_game_with_players(
            p1_actions=[(ActionType.ALL_IN, None)],
            p2_actions=[(ActionType.FOLD, None)],
            stacks=(30, 500),  # p1 short-stacked so all-in is realistic
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        # state_type is serialized as its integer value; ALL_IN = 3
        ALL_IN_VALUE = 3

        def _has_allin_player(payload):
            for player_data in payload.get("after", {}).get("players", []):
                if player_data.get("state", {}).get("state_type") == ALL_IN_VALUE:
                    return True
            return False

        self.assertTrue(
            any(_has_allin_player(e.payload) for e in events),
            "No GAME_STATE_CHANGED event captured the all-in transition",
        )

    def test_game_state_changed_emitted_when_player_loses_chips(self):
        """GAME_STATE_CHANGED must be emitted when a player loses chips (call)."""
        game, p1, p2 = self._make_game_with_players(
            p1_actions=[(ActionType.CALL, None), (ActionType.CHECK, None),
                        (ActionType.CHECK, None), (ActionType.CHECK, None)],
            p2_actions=[(ActionType.CHECK, None), (ActionType.CHECK, None),
                        (ActionType.CHECK, None), (ActionType.CHECK, None)],
        )
        stack_snapshots = []

        def record(event, game):
            for pd in event.payload.get("after", {}).get("players", []):
                stack_snapshots.append(pd.get("state", {}).get("stack"))

        game.subscribe(GameEventType.GAME_STATE_CHANGED, record)
        game.start()

        # Should contain various stack values (not all the same)
        unique_stacks = set(s for s in stack_snapshots if s is not None)
        self.assertGreater(len(unique_stacks), 1, "Stack values never changed across events")

    def test_game_state_changed_emitted_when_player_gains_chips(self):
        """GAME_STATE_CHANGED must be emitted when a player wins the pot."""
        game, p1, p2 = self._make_game_with_players(
            p1_actions=[(ActionType.FOLD, None)],
            p2_actions=[],
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        initial_stacks = {p.uid: p.state.stack for p in game.state.players}
        game.start()

        # Find the event where the winner's stack increased
        def _stack_increased(payload):
            for player_data in payload.get("after", {}).get("players", []):
                uid = player_data.get("uid")
                new_stack = player_data.get("state", {}).get("stack", 0)
                if uid and new_stack > initial_stacks.get(uid, 0):
                    return True
            return False

        self.assertTrue(
            any(_stack_increased(e.payload) for e in events),
            "No GAME_STATE_CHANGED event captured a stack increase (pot win)",
        )

    def test_player_state_is_frozen(self):
        """Assigning to player.state.x directly must raise a ValidationError."""
        from pydantic import ValidationError
        from maverick import PlayerState

        ps = PlayerState(stack=100)
        with self.assertRaises(ValidationError):
            ps.stack = 200


class TestCommunityCardStateChangedEvents(unittest.TestCase):
    """Test that GAME_STATE_CHANGED is emitted when community cards are dealt."""

    def _make_game_with_players(self, p1_actions, p2_actions):
        game = Game(small_blind=10, big_blind=20, max_hands=1, first_button_position=0)
        p1 = MockPlayer(
            id="p1",
            name="P1",
            state=PlayerState(stack=500),
            actions=p1_actions,
        )
        p2 = MockPlayer(
            id="p2",
            name="P2",
            state=PlayerState(stack=500),
            actions=p2_actions,
        )
        game.add_player(p1)
        game.add_player(p2)
        return game

    def _community_card_counts(self, payload):
        """Return (before_count, after_count) of community_cards in a payload."""
        before = len(payload.get("before", {}).get("community_cards", []))
        after = len(payload.get("after", {}).get("community_cards", []))
        return before, after

    def test_game_state_changed_emitted_on_flop(self):
        """GAME_STATE_CHANGED must be emitted when the flop is dealt (0 → 3 cards)."""
        game = self._make_game_with_players(
            p1_actions=[
                (ActionType.CALL, None),   # pre-flop call
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
            p2_actions=[
                (ActionType.CHECK, None),  # pre-flop check
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        flop_events = [
            e for e in events
            if self._community_card_counts(e.payload) == (0, 3)
        ]
        self.assertTrue(
            len(flop_events) > 0,
            "No GAME_STATE_CHANGED event captured the flop deal (0 → 3 community cards)",
        )

    def test_game_state_changed_emitted_on_turn(self):
        """GAME_STATE_CHANGED must be emitted when the turn is dealt (3 → 4 cards)."""
        game = self._make_game_with_players(
            p1_actions=[
                (ActionType.CALL, None),   # pre-flop call
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
            p2_actions=[
                (ActionType.CHECK, None),  # pre-flop check
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        turn_events = [
            e for e in events
            if self._community_card_counts(e.payload) == (3, 4)
        ]
        self.assertTrue(
            len(turn_events) > 0,
            "No GAME_STATE_CHANGED event captured the turn deal (3 → 4 community cards)",
        )

    def test_game_state_changed_emitted_on_river(self):
        """GAME_STATE_CHANGED must be emitted when the river is dealt (4 → 5 cards)."""
        game = self._make_game_with_players(
            p1_actions=[
                (ActionType.CALL, None),   # pre-flop call
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
            p2_actions=[
                (ActionType.CHECK, None),  # pre-flop check
                (ActionType.CHECK, None),  # flop
                (ActionType.CHECK, None),  # turn
                (ActionType.CHECK, None),  # river
            ],
        )
        events = []
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: events.append(e))
        game.start()

        river_events = [
            e for e in events
            if self._community_card_counts(e.payload) == (4, 5)
        ]
        self.assertTrue(
            len(river_events) > 0,
            "No GAME_STATE_CHANGED event captured the river deal (4 → 5 community cards)",
        )


if __name__ == "__main__":
    unittest.main()
