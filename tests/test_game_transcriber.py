"""Tests for GameTranscriber."""

import unittest

from maverick import Game, ActionType, Player, PlayerAction, PlayerState
from maverick.listeners.game_transcriber import GameTranscriber


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


def _make_game(max_hands=1, p1_actions=None, p2_actions=None):
    game = Game(small_blind=10, big_blind=20, max_hands=max_hands, first_button_position=0)
    p1 = MockPlayer(uid="p1", name="Alice", actions=p1_actions or [(ActionType.FOLD, None)])
    p2 = MockPlayer(uid="p2", name="Bob", actions=p2_actions or [(ActionType.FOLD, None)])
    game.add_player(p1, state=PlayerState(stack=500))
    game.add_player(p2, state=PlayerState(stack=500))
    return game, p1, p2


class TestGameTranscriberInit(unittest.TestCase):
    def test_history_empty_before_game_starts(self):
        game, _, _ = _make_game()
        transcriber = GameTranscriber(game)
        self.assertEqual(transcriber.history, "")

    def test_event_dump_empty_before_game_starts(self):
        game, _, _ = _make_game()
        transcriber = GameTranscriber(game)
        self.assertEqual(transcriber.event_dump, [])

    def test_listen_none_does_nothing(self):
        transcriber = GameTranscriber(None)
        self.assertEqual(transcriber.history, "")

    def test_listen_after_construction(self):
        game, _, _ = _make_game()
        transcriber = GameTranscriber()
        transcriber.listen(game)
        game.start()
        self.assertGreater(len(transcriber.history), 0)


class TestGameTranscriberHistory(unittest.TestCase):
    def setUp(self):
        self.game, self.p1, self.p2 = _make_game()
        self.transcriber = GameTranscriber(self.game)
        self.game.start()

    def test_history_is_non_empty_after_game(self):
        self.assertGreater(len(self.transcriber.history), 0)

    def test_history_is_string(self):
        self.assertIsInstance(self.transcriber.history, str)

    def test_history_contains_game_started(self):
        self.assertIn("Game Started", self.transcriber.history)

    def test_history_contains_player_names(self):
        self.assertIn("Alice", self.transcriber.history)
        self.assertIn("Bob", self.transcriber.history)

    def test_history_contains_blind_info(self):
        self.assertIn("Small blind: 10", self.transcriber.history)
        self.assertIn("Big blind: 20", self.transcriber.history)

    def test_history_contains_hand_section(self):
        self.assertIn("Hand 1", self.transcriber.history)

    def test_history_contains_button_info(self):
        self.assertIn("is on the button", self.transcriber.history)

    def test_history_contains_blind_positions(self):
        self.assertIn("is the small blind", self.transcriber.history)
        self.assertIn("is the big blind", self.transcriber.history)

    def test_history_contains_fold_action(self):
        self.assertIn("folds", self.transcriber.history)


class TestGameTranscriberEventDump(unittest.TestCase):
    def setUp(self):
        self.game, _, _ = _make_game()
        self.transcriber = GameTranscriber(self.game)
        self.game.start()

    def test_event_dump_non_empty_after_game(self):
        self.assertGreater(len(self.transcriber.event_dump), 0)

    def test_event_dump_entries_are_dicts(self):
        for entry in self.transcriber.event_dump:
            self.assertIsInstance(entry, dict)

    def test_event_dump_entries_have_uid_and_ts(self):
        for entry in self.transcriber.event_dump:
            self.assertIn("uid", entry)
            self.assertIn("ts", entry)


class TestGameTranscriberActions(unittest.TestCase):
    def _run(self, p1_actions, p2_actions):
        game, _, _ = _make_game(p1_actions=p1_actions, p2_actions=p2_actions)
        transcriber = GameTranscriber(game)
        game.start()
        return transcriber.history

    def test_call_action_logged(self):
        history = self._run(
            p1_actions=[(ActionType.CALL, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
            p2_actions=[(ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
        )
        self.assertIn("calls", history)

    def test_check_action_logged(self):
        history = self._run(
            p1_actions=[(ActionType.CALL, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
            p2_actions=[(ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
        )
        self.assertIn("checks", history)

    def test_raise_action_logged(self):
        history = self._run(
            p1_actions=[(ActionType.RAISE, 40), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
            p2_actions=[(ActionType.CALL, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
        )
        self.assertIn("raises", history)

    def test_pot_won_logged(self):
        history = self._run(
            p1_actions=[(ActionType.FOLD, None)],
            p2_actions=[],
        )
        self.assertIn("wins", history)

    def test_showdown_logged(self):
        history = self._run(
            p1_actions=[(ActionType.CALL, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
            p2_actions=[(ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None), (ActionType.CHECK, None)],
        )
        self.assertIn("SHOWDOWN", history)


class TestGameTranscriberSectionHeaders(unittest.TestCase):
    def test_section_header_fills_max_line_length(self):
        game, _, _ = _make_game()
        transcriber = GameTranscriber(game)
        game.start()
        lines = transcriber.history.splitlines()
        header_lines = [l for l in lines if set(l) <= {"=", "-", " "} and len(l) > 0]
        for line in header_lines:
            self.assertLessEqual(len(line), transcriber.max_line_length)

    def test_multi_hand_contains_multiple_hand_headers(self):
        game = Game(small_blind=10, big_blind=20, max_hands=3, first_button_position=0)
        p1 = MockPlayer(uid="p1", name="Alice")
        p2 = MockPlayer(uid="p2", name="Bob")
        game.add_player(p1, state=PlayerState(stack=500))
        game.add_player(p2, state=PlayerState(stack=500))
        transcriber = GameTranscriber(game)
        game.start()

        self.assertIn("Hand 1", transcriber.history)
        self.assertIn("Hand 2", transcriber.history)
        self.assertIn("Hand 3", transcriber.history)


if __name__ == "__main__":
    unittest.main()
