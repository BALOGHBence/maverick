"""Comprehensive tests for the Game class."""

import unittest

from maverick import (
    Game,
    Player,
    PlayerState,
    PlayerAction,
    ActionType,
    GameEventType,
    GameEvent,
)
from maverick.enums import GameStateType


class SimpleTestPlayer(Player):
    """A simple test player that always folds."""

    def decide_action(
        self,
        *,
        game,
        valid_actions,
        min_raise_amount,
        call_amount,
        min_bet_amount,
    ):
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)


DEFAULT_SMALL_BLIND = 10
DEFAULT_BIG_BLIND = 20


def create_game(**kwargs) -> Game:
    base_kwargs = {
        "small_blind": DEFAULT_SMALL_BLIND,
        "big_blind": DEFAULT_BIG_BLIND,
    }
    base_kwargs.update(kwargs)
    return Game(**base_kwargs)


class TestGameInitialization(unittest.TestCase):
    """Test Game initialization."""

    def test_game_init_with_defaults(self):
        """Test game initialization with default parameters."""
        game = create_game()
        self.assertEqual(game.state.small_blind, 10)
        self.assertEqual(game.state.big_blind, 20)
        self.assertEqual(game.rules.dealing.min_players, 2)
        self.assertEqual(game.rules.dealing.max_players, 9)
        self.assertEqual(game.max_hands, 1000)

    def test_game_init_with_custom_parameters(self):
        """Test game initialization with custom parameters."""
        game = create_game(
            small_blind=5,
            big_blind=10,
            min_players=3,
            max_players=6,
            max_hands=50,
            exc_handling_mode="raise",
        )
        self.assertEqual(game.state.small_blind, 5)
        self.assertEqual(game.state.big_blind, 10)
        self.assertEqual(game.rules.dealing.min_players, 3)
        self.assertEqual(game.rules.dealing.max_players, 6)
        self.assertEqual(game.max_hands, 50)
        self.assertTrue(game._events._strict)

    def test_game_init_creates_event_queue(self):
        """Test that game initialization creates an empty event queue."""
        game = create_game()
        self.assertEqual(len(game._event_queue), 0)


class TestAddPlayer(unittest.TestCase):
    """Test Game.add_player method."""

    def test_add_player_to_empty_game(self):
        """Test adding a player to an empty game."""
        game = create_game()
        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)
        self.assertEqual(len(game.state.players), 1)
        self.assertEqual(game.state.players[0].id, "p1")

    def test_add_player_assigns_seat(self):
        """Test that add_player assigns a seat to the player."""
        game = create_game()
        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)
        self.assertIsNotNone(player.state)
        self.assertIsNotNone(player.state.seat)
        self.assertEqual(player.state.seat, 0)

    def test_add_multiple_players(self):
        """Test adding multiple players."""
        game = create_game()
        p1 = SimpleTestPlayer(id="p1", name="Player1")
        p2 = SimpleTestPlayer(id="p2", name="Player2")
        game.add_player(p1)
        game.add_player(p2)
        self.assertEqual(len(game.state.players), 2)
        self.assertEqual(p1.state.seat, 0)
        self.assertEqual(p2.state.seat, 1)

    def test_add_player_to_full_table_raises_error(self):
        """Test that adding a player to a full table raises ValueError."""
        game = create_game(max_players=2)
        p1 = SimpleTestPlayer(id="p1", name="Player1")
        p2 = SimpleTestPlayer(id="p2", name="Player2")
        p3 = SimpleTestPlayer(id="p3", name="Player3")

        game.add_player(p1)
        game.add_player(p2)

        with self.assertRaises(ValueError) as context:
            game.add_player(p3)
        self.assertIn("Table is full", str(context.exception))

    def test_add_player_with_existing_state(self):
        """Test adding a player with an existing PlayerState."""
        game = create_game()
        player = SimpleTestPlayer(
            id="p1",
            name="Player1",
            state=PlayerState(stack=500, seat=None),
        )
        game.add_player(player)
        self.assertEqual(len(game.state.players), 1)
        self.assertEqual(player.state.stack, 500)
        self.assertEqual(player.state.seat, 0)

    def test_add_player_emits_event(self):
        """Test that adding a player emits PLAYER_JOINED event."""
        game = create_game()
        events = []

        def record_event(event: GameEvent, game: Game):
            events.append(event)

        game.subscribe(GameEventType.PLAYER_JOINED, record_event)

        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, GameEventType.PLAYER_JOINED)
        self.assertEqual(events[0].player_id, "p1")


class TestRemovePlayer(unittest.TestCase):
    """Test Game.remove_player method."""

    def test_remove_player_from_waiting_game(self):
        """Test removing a player from a game in WAITING_FOR_PLAYERS state."""
        game = create_game()
        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)

        game.remove_player(player)
        self.assertEqual(len(game.state.players), 0)

    def test_remove_nonexistent_player_raises_error(self):
        """Test removing a player that doesn't exist raises ValueError."""
        game = create_game()
        player = SimpleTestPlayer(id="p1", name="Player1")

        with self.assertRaises(ValueError) as context:
            game.remove_player(player)
        self.assertIn("not found", str(context.exception))

    def test_remove_player_emits_event(self):
        """Test that removing a player emits PLAYER_LEFT event."""
        game = create_game()
        events = []

        def record_event(event: GameEvent, game: Game):
            events.append(event)

        game.subscribe(GameEventType.PLAYER_LEFT, record_event)

        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)
        game.remove_player(player)

        # Find the PLAYER_LEFT event
        left_events = [e for e in events if e.type == GameEventType.PLAYER_LEFT]
        self.assertEqual(len(left_events), 1)
        self.assertEqual(left_events[0].player_id, "p1")

    def test_remove_player_updates_player_list(self):
        """Test that removing a player updates the player list correctly."""
        game = create_game()
        p1 = SimpleTestPlayer(id="p1", name="Player1")
        p2 = SimpleTestPlayer(id="p2", name="Player2")
        game.add_player(p1)
        game.add_player(p2)

        game.remove_player(p1)

        self.assertEqual(len(game.state.players), 1)
        self.assertEqual(game.state.players[0].id, "p2")

    def remove_player_while_hand_is_in_progress_raises_error(self):
        """Test that removing a player while a hand is in progress raises ValueError."""
        game = create_game()
        player = SimpleTestPlayer(id="p1", name="Player1")
        game.add_player(player)

        # Simulate hand in progress
        game._initialize_game()
        game.state.state_type = GameStateType.STARTED

        with self.assertRaises(ValueError) as context:
            game.remove_player(player)
        self.assertIn(
            "Cannot remove players while a hand is in progress", str(context.exception)
        )


class TestSubscribeUnsubscribe(unittest.TestCase):
    """Test Game.subscribe and unsubscribe methods."""

    def test_subscribe_returns_token(self):
        """Test that subscribe returns a token string."""
        game = create_game()

        def handler(event: GameEvent, game: Game):
            pass

        token = game.subscribe(GameEventType.GAME_STARTED, handler)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_subscribe_handler_called_on_event(self):
        """Test that subscribed handler is called when event occurs."""
        game = create_game(max_hands=1)
        call_count = [0]

        def handler(event: GameEvent, game: Game):
            call_count[0] += 1

        game.subscribe(GameEventType.GAME_STARTED, handler)

        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)
        game.start()

        self.assertEqual(call_count[0], 1)

    def test_unsubscribe_removes_handler(self):
        """Test that unsubscribe removes a handler."""
        game = create_game(max_hands=1)
        call_count = [0]

        def handler(event: GameEvent, game: Game):
            call_count[0] += 1

        token = game.subscribe(GameEventType.GAME_STARTED, handler)
        game.unsubscribe(token)

        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)
        game.start()

        self.assertEqual(call_count[0], 0)

    def test_multiple_handlers_for_same_event(self):
        """Test subscribing multiple handlers for the same event."""
        game = create_game(max_hands=1)
        calls = []

        def handler1(event: GameEvent, game: Game):
            calls.append(1)

        def handler2(event: GameEvent, game: Game):
            calls.append(2)

        game.subscribe(GameEventType.GAME_STARTED, handler1)
        game.subscribe(GameEventType.GAME_STARTED, handler2)

        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)
        game.start()

        self.assertIn(1, calls)
        self.assertIn(2, calls)


class TestStepAndHasEvents(unittest.TestCase):
    """Test Game.step and has_events methods."""

    def test_has_events_returns_false_for_empty_queue(self):
        """Test has_events returns False when queue is empty."""
        game = create_game()
        self.assertFalse(game.has_events())

    def test_has_events_returns_true_when_events_queued(self):
        """Test has_events returns True when events are in queue."""
        game = create_game()
        game._event_queue.append(GameEventType.GAME_STARTED)
        self.assertTrue(game.has_events())

    def test_step_processes_event(self):
        """Test step processes an event from the queue."""
        game = create_game()
        game._initialize_game()
        game.state.state_type = GameStateType.READY

        # Add players so _start_new_hand doesn't fail
        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)

        game._event_queue.append(GameEventType.GAME_STARTED)

        result = game.step()
        self.assertTrue(result)
        # Event queue may have more events after processing GAME_STARTED

    def test_step_returns_false_when_no_events(self):
        """Test step returns False when no events to process."""
        game = create_game()
        result = game.step()
        self.assertFalse(result)


class TestGameStart(unittest.TestCase):
    """Test Game.start method."""

    def test_start_with_enough_players(self):
        """Test starting a game with enough players."""
        game = create_game(max_hands=1)
        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)

        game.start()

        self.assertEqual(game.state.hand_number, 1)

    def test_start_emits_game_started_event(self):
        """Test that start emits GAME_STARTED event."""
        game = create_game(max_hands=1)
        events = []

        def record_event(event: GameEvent, game: Game):
            events.append(event)

        game.subscribe(GameEventType.GAME_STARTED, record_event)

        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)
        game.start()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, GameEventType.GAME_STARTED)


class TestCreateEvent(unittest.TestCase):
    """Test Game._create_event method."""

    def test_create_event_basic(self):
        """Test creating a basic event."""
        game = create_game()
        game.state.hand_number = 5

        event = game._create_event(GameEventType.GAME_STARTED)

        self.assertEqual(event.type, GameEventType.GAME_STARTED)
        self.assertEqual(event.hand_number, 5)
        self.assertIsNotNone(event.street)

    def test_create_event_with_player_id(self):
        """Test creating an event with player_id."""
        game = create_game()

        event = game._create_event(
            GameEventType.PLAYER_ACTION_TAKEN,
            player_id="p1",
        )

        self.assertEqual(event.type, GameEventType.PLAYER_ACTION_TAKEN)
        self.assertEqual(event.player_id, "p1")

    def test_create_event_with_action(self):
        """Test creating an event with action."""
        game = create_game()
        action = PlayerAction(player_id="p1", action_type=ActionType.FOLD)

        event = game._create_event(
            GameEventType.PLAYER_ACTION_TAKEN,
            player_id="p1",
            action=action,
        )

        self.assertEqual(event.type, GameEventType.PLAYER_ACTION_TAKEN)
        self.assertEqual(event.action, action)


class TestEmitMethod(unittest.TestCase):
    """Test Game._emit method."""

    def test_emit_calls_handlers(self):
        """Test that _emit calls subscribed handlers."""
        game = create_game()
        calls = []

        def handler(event: GameEvent, game: Game):
            calls.append(event.type)

        game.subscribe(GameEventType.GAME_STARTED, handler)

        event = game._create_event(GameEventType.GAME_STARTED)
        game._emit(event)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], GameEventType.GAME_STARTED)

    def test_emit_calls_player_on_event_hook(self):
        """Test that _emit calls player on_event hooks."""

        class ObservantPlayer(SimpleTestPlayer):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                object.__setattr__(self, "events_seen", [])

            def on_event(self, event: GameEvent, game: Game):
                self.events_seen.append(event.type)

        game = create_game()
        player = ObservantPlayer(id="p1", name="P1")
        game.add_player(player)

        event = game._create_event(GameEventType.GAME_STARTED)
        game._emit(event)

        self.assertIn(GameEventType.GAME_STARTED, player.events_seen)


class TestInitializeGame(unittest.TestCase):
    """Test Game._initialize_game method."""

    def test_initialize_game_resets_hand_number(self):
        """Test that _initialize_game sets hand_number to 0."""
        game = create_game()
        game.state.hand_number = 5

        game._initialize_game()

        self.assertEqual(game.state.hand_number, 0)


class TestGameEdgeCases(unittest.TestCase):
    """Test edge cases in Game class."""

    def test_add_player_during_game_raises_error(self):
        """Test that adding a player during a game raises ValueError."""
        game = create_game(max_hands=1)
        p1 = SimpleTestPlayer(id="p1", name="P1", state=PlayerState(stack=100))
        p2 = SimpleTestPlayer(id="p2", name="P2", state=PlayerState(stack=100))
        game.add_player(p1)
        game.add_player(p2)

        # Start the game (changes state from WAITING/READY)
        game._initialize_game()
        game.state.state_type = GameStateType.STARTED

        p3 = SimpleTestPlayer(id="p3", name="P3", state=PlayerState(stack=100))
        with self.assertRaises(ValueError) as context:
            game.add_player(p3)
        self.assertIn(
            "Cannot add players while game is in progress", str(context.exception)
        )

    def test_game_with_strict_mode(self):
        """Test game initialization with strict mode enabled."""
        game = create_game(exc_handling_mode="raise")
        self.assertTrue(game._events._strict)


class TestGameLoggingEvents(unittest.TestCase):
    """Test Game logging events functionality."""

    def test_game_logging_events_disabled(self):
        """Test that game does not log events when logging is disabled."""
        game = create_game(log_events=False)
        self.assertFalse(game._log_events)

        # Create an event and emit it
        event = game._create_event(GameEventType.GAME_STARTED)
        game._emit(event)


if __name__ == "__main__":
    unittest.main()
