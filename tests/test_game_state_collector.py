"""Tests for GameStateCollector."""

import unittest

from maverick import Game, GameEventType, ActionType, Player, PlayerAction, PlayerState
from maverick.listeners.game_state_collector import GameStateCollector


class MockPlayer(Player):
    def __init__(self, actions=None, **kwargs):
        super().__init__(**kwargs)
        self._actions = actions or []
        self._action_index = 0

    def decide_action(self, *, game, valid_actions, min_raise_amount, call_amount, min_bet_amount) -> PlayerAction:
        if self._action_index < len(self._actions):
            action_type, amount = self._actions[self._action_index]
            self._action_index += 1
            return PlayerAction(player_uid=self.uid, action_type=action_type, amount=amount or 0)
        return PlayerAction(player_uid=self.uid, action_type=ActionType.FOLD)


def _make_game(max_hands=1):
    game = Game(small_blind=10, big_blind=20, max_hands=max_hands, first_button_position=0)
    p1 = MockPlayer(uid="p1", name="P1", actions=[(ActionType.FOLD, None)])
    p2 = MockPlayer(uid="p2", name="P2", actions=[(ActionType.FOLD, None)])
    game.add_player(p1, state=PlayerState(stack=500))
    game.add_player(p2, state=PlayerState(stack=500))
    return game


class TestGameStateCollectorInit(unittest.TestCase):
    def test_states_empty_before_game_starts(self):
        game = _make_game()
        collector = GameStateCollector(game)
        self.assertEqual(collector.states, [])

    def test_listen_none_does_nothing(self):
        collector = GameStateCollector(None)
        self.assertEqual(collector.states, [])

    def test_no_game_at_construction_then_listen_later(self):
        game = _make_game()
        collector = GameStateCollector()
        collector.listen(game)
        game.start()
        self.assertGreater(len(collector.states), 0)


class TestGameStateCollectorCollection(unittest.TestCase):
    def setUp(self):
        self.game = _make_game()
        self.collector = GameStateCollector(self.game)
        self.game.start()

    def test_collects_at_least_one_state(self):
        self.assertGreater(len(self.collector.states), 0)

    def test_every_entry_has_ts(self):
        for entry in self.collector.states:
            self.assertIn("ts", entry)

    def test_every_entry_has_event_uid(self):
        for entry in self.collector.states:
            self.assertIn("event_uid", entry)

    def test_every_entry_has_game_state_fields(self):
        for entry in self.collector.states:
            self.assertIn("hand_number", entry)
            self.assertIn("pot", entry)
            self.assertIn("players", entry)

    def test_ts_is_float_and_event_uid_is_string(self):
        for entry in self.collector.states:
            self.assertIsInstance(entry["ts"], float)
            self.assertIsInstance(entry["event_uid"], str)

    def test_event_uid_values_are_unique(self):
        uids = [entry["event_uid"] for entry in self.collector.states]
        self.assertEqual(len(uids), len(set(uids)))


class TestGameStateCollectorVsEventCount(unittest.TestCase):
    def test_one_state_per_event(self):
        """Number of collected states must equal the number of events emitted."""
        game = _make_game()
        event_count = 0

        def count(event, g):
            nonlocal event_count
            event_count += 1

        for event_type in GameEventType:
            game.subscribe(event_type, count)

        collector = GameStateCollector(game)
        game.start()

        self.assertEqual(len(collector.states), event_count)


class TestGameStateCollectorMultiHand(unittest.TestCase):
    def test_collects_across_multiple_hands(self):
        game = Game(small_blind=10, big_blind=20, max_hands=3, first_button_position=0)
        p1 = MockPlayer(uid="p1", name="P1")
        p2 = MockPlayer(uid="p2", name="P2")
        game.add_player(p1, state=PlayerState(stack=500))
        game.add_player(p2, state=PlayerState(stack=500))

        single_game = _make_game(max_hands=1)
        single_collector = GameStateCollector(single_game)
        single_game.start()
        single_count = len(single_collector.states)

        collector = GameStateCollector(game)
        game.start()

        self.assertGreater(len(collector.states), single_count)


class TestGameStateCollectorEventTypeFilter(unittest.TestCase):
    def test_single_event_type_only_collects_that_type(self):
        """Only states triggered by the specified event type are collected."""
        game = _make_game()
        collector = GameStateCollector(game, event_types=[GameEventType.HAND_STARTED])
        game.start()

        self.assertEqual(len(collector.states), 1)

    def test_two_event_types_collects_both(self):
        game = _make_game()
        collector = GameStateCollector(
            game,
            event_types=[GameEventType.HAND_STARTED, GameEventType.HAND_ENDED],
        )
        game.start()

        self.assertEqual(len(collector.states), 2)

    def test_filtered_collector_collects_fewer_than_unfiltered(self):
        game_all = _make_game()
        game_filtered = _make_game()

        collector_all = GameStateCollector(game_all)
        collector_filtered = GameStateCollector(
            game_filtered, event_types=[GameEventType.HAND_STARTED]
        )

        game_all.start()
        game_filtered.start()

        self.assertLess(len(collector_filtered.states), len(collector_all.states))

    def test_listen_with_event_types_after_construction(self):
        game = _make_game()
        collector = GameStateCollector()
        collector.listen(game, event_types=[GameEventType.HAND_STARTED])
        game.start()

        self.assertEqual(len(collector.states), 1)

    def test_empty_event_types_list_collects_nothing(self):
        game = _make_game()
        collector = GameStateCollector(game, event_types=[])
        game.start()

        self.assertEqual(len(collector.states), 0)

    def test_invalid_event_type_raises_type_error(self):
        game = _make_game()
        with self.assertRaises(TypeError):
            GameStateCollector(game, event_types=["HAND_STARTED"])

    def test_invalid_event_type_in_listen_raises_type_error(self):
        game = _make_game()
        collector = GameStateCollector()
        with self.assertRaises(TypeError):
            collector.listen(game, event_types=[42])

    def test_mixed_valid_and_invalid_raises_type_error(self):
        game = _make_game()
        with self.assertRaises(TypeError):
            GameStateCollector(
                game,
                event_types=[GameEventType.HAND_STARTED, "HAND_ENDED"],
            )

    def test_none_event_types_collects_all(self):
        """Passing event_types=None explicitly should behave like the default (all events)."""
        game_default = _make_game()
        game_explicit = _make_game()

        collector_default = GameStateCollector(game_default)
        collector_explicit = GameStateCollector(game_explicit, event_types=None)

        game_default.start()
        game_explicit.start()

        self.assertEqual(len(collector_default.states), len(collector_explicit.states))


if __name__ == "__main__":
    unittest.main()
