"""Tests for saving games to disk, resuming them and replaying them (issue #103)."""

import json
import logging
import os
import subprocess  # nosec B404 - runs the test interpreter only
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from pydantic import ValidationError

from maverick import (
    ActionType,
    Game,
    GameEventType,
    GameStage,
    Player,
    PlayerAction,
    PlayerState,
    Replay,
    SaveFormatError,
)
from maverick.players import AggressiveBot, CallBot
from maverick.rules import DealingRules, PokerRules, ShowdownRules, StakesRules
from maverick.savegame import (
    CHECKPOINT_FILE,
    EVENTS_FILE,
    HEADER_FILE,
    SAVE_FORMAT_VERSION,
)

TESTS_DIR = Path(__file__).resolve().parent


class CountingBot(Player):
    """Deterministic bot whose decisions depend on the state it exports."""

    register = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.decisions = 0

    def decide_action(self, *, valid_actions, min_raise_amount, **_) -> PlayerAction:
        self.decisions += 1
        if self.decisions % 4 == 0 and ActionType.RAISE in valid_actions:
            return PlayerAction(
                player_uid=self.uid,
                action_type=ActionType.RAISE,
                amount=min_raise_amount,
            )
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_uid=self.uid, action_type=ActionType.CHECK)
        return PlayerAction(player_uid=self.uid, action_type=ActionType.CALL)

    def export_state(self):
        return {"decisions": self.decisions}

    def import_state(self, state):
        self.decisions = state["decisions"]


class ResumeHookBot(CallBot):
    """Records the GAME_RESUMED events it receives in its exported state."""

    register = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resumed: list[int] = []
        self.history_types: list[str] = []

    def on_game_resumed(self, event, game) -> None:
        self.resumed.append(event.hand_number)
        self.history_types = [e.type.name for e in game.history]

    def export_state(self):
        return {"resumed": self.resumed, "history_types": self.history_types}

    def import_state(self, state):
        self.resumed = state["resumed"]


class FailingExportBot(CallBot):
    register = False

    def export_state(self):
        raise RuntimeError("no state today")


class WrongExportBot(CallBot):
    register = False

    def export_state(self):
        return ["not", "a", "dict"]


class KillerBot(CallBot):
    """Kills the process it runs in when hand ``kill_at`` starts."""

    register = False

    def __init__(self, kill_at: int, **kwargs):
        super().__init__(**kwargs)
        self.kill_at = kill_at

    def decide_action(self, *, game, **kwargs) -> PlayerAction:
        if game.state.hand_number >= self.kill_at:
            os._exit(17)
        return super().decide_action(game=game, **kwargs)


def _players() -> list:
    return [
        CountingBot(name="counter", uid="u-counter"),
        CallBot(name="caller", uid="u-caller"),
        AggressiveBot(name="aggressor", uid="u-aggressor"),
    ]


def _new_game(players, *, stack: int = 300, **kwargs) -> Game:
    kwargs.setdefault("seed", 2024)
    kwargs.setdefault("log_events", False)
    game = Game(small_blind=1, big_blind=2, **kwargs)
    for player in players:
        game.add_player(player, state=PlayerState(stack=stack))
    return game


def _comparable(state) -> dict:
    """A game state without the fields that differ between any two copies."""
    return state.model_dump(mode="json", exclude={"uid", "ts"})


def _dealt_cards(replay: Replay) -> dict:
    """Hole cards and board of every hand, as dealt."""
    cards = {}
    for event, state in replay:
        if event.type == GameEventType.SHOWDOWN_COMPLETED:
            cards[event.hand_number] = (
                [c.code() for c in state.community_cards],
                {
                    p.uid: [c.code() for c in p.state.holding.cards]
                    for p in state.players
                    if p.state.holding is not None
                },
            )
    return cards


class SaveTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)


class TestResume(SaveTestCase):
    def _check_resume_matches_uninterrupted_game(self, isolation: str) -> None:
        reference = _new_game(
            _players(),
            max_hands=10,
            save_dir=self.dir / "reference",
            player_isolation=isolation,
        )
        reference.start()

        first = _new_game(
            _players(),
            max_hands=5,
            save_dir=self.dir / "split",
            player_isolation=isolation,
        )
        first.start()
        self.assertEqual(first.state.hand_number, 5)

        second = Game.load(
            self.dir / "split",
            players=_players(),
            max_hands=10,
            log_events=False,
            player_isolation=isolation,
        )
        self.assertEqual(second.uid, first.uid)
        self.assertEqual(second.seed, first.seed)
        second.start()

        self.assertEqual(second.state.stage, GameStage.GAME_OVER)
        self.assertEqual(_comparable(second.state), _comparable(reference.state))
        self.assertEqual(
            second.get_player_state("u-counter"),
            reference.get_player_state("u-counter"),
        )

        expected, resumed = Replay(self.dir / "reference"), Replay(self.dir / "split")
        self.assertEqual(_dealt_cards(resumed), _dealt_cards(expected))
        self.assertEqual(len(_dealt_cards(expected)), 10)
        # The same events, plus the marker where the game was resumed
        types = [e.type for e in resumed.events if e.type != GameEventType.GAME_RESUMED]
        self.assertEqual(types, [e.type for e in expected.events])
        self.assertEqual(
            [
                e.hand_number
                for e in resumed.events
                if e.type == GameEventType.GAME_RESUMED
            ],
            [5],
        )
        self.assertEqual(resumed.hand_numbers, list(range(1, 11)))

    def test_resume_matches_uninterrupted_game_in_process(self):
        self._check_resume_matches_uninterrupted_game("none")

    def test_resume_matches_uninterrupted_game_isolated(self):
        self._check_resume_matches_uninterrupted_game("process")

    def test_game_without_save_deals_the_same_cards(self):
        saved = _new_game(_players(), max_hands=4, save_dir=self.dir / "saved")
        saved.start()
        unsaved = _new_game(_players(), max_hands=4)
        unsaved.start()
        self.assertEqual(_comparable(saved.state), _comparable(unsaved.state))
        self.assertIsNone(unsaved.save_dir)
        self.assertEqual(saved.save_dir, self.dir / "saved")

    def test_resumed_game_keeps_its_history_and_receives_game_resumed(self):
        players = [ResumeHookBot(name="hook", uid="u-hook"), CallBot(name="b", uid="b")]
        _new_game(players, max_hands=2, save_dir=self.dir / "s").start()

        loaded = Game.load(
            self.dir / "s",
            players=[
                ResumeHookBot(name="hook", uid="u-hook"),
                CallBot(name="b", uid="b"),
            ],
            max_hands=3,
            log_events=False,
        )
        # The history of the loaded game is the saved one, without GAME_ENDED
        self.assertEqual(loaded.history[0].type, GameEventType.PLAYER_JOINED)
        self.assertEqual(loaded.history[-1].type, GameEventType.HAND_ENDED)
        received = []
        loaded.subscribe(GameEventType.GAME_RESUMED, lambda e, g: received.append(e))
        loaded.start()

        self.assertEqual([e.hand_number for e in received], [2])
        state = loaded.get_player_state("u-hook")
        self.assertEqual(state["resumed"], [2])
        self.assertEqual(state["history_types"][0], "PLAYER_JOINED")
        self.assertEqual(state["history_types"][-1], "GAME_RESUMED")
        self.assertEqual(loaded.state.hand_number, 3)

    def test_finished_game_can_be_extended_or_ends_again(self):
        _new_game(_players(), max_hands=2, save_dir=self.dir / "s").start()

        again = Game.load(self.dir / "s", players=_players(), log_events=False)
        again.start()
        self.assertEqual(again.state.stage, GameStage.GAME_OVER)
        self.assertEqual(again.state.hand_number, 2)
        self.assertEqual(
            [e.type for e in again.history[-2:]],
            [GameEventType.GAME_RESUMED, GameEventType.GAME_ENDED],
        )

    def test_resume_before_the_first_hand_ended(self):
        players = [CallBot(name="a", uid="a"), KillerBot(1, name="k", uid="k")]
        game = _new_game(players, max_hands=3, save_dir=self.dir / "s")
        with mock.patch("os._exit", side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                game.start()
        game.close()

        loaded = Game.load(
            self.dir / "s",
            players=[CallBot(name="a", uid="a"), CallBot(name="k", uid="k")],
            log_events=False,
        )
        self.assertEqual(loaded.state.stage, GameStage.STARTED)
        self.assertEqual(loaded.state.hand_number, 0)
        loaded.start()

        reference = _new_game(
            [CallBot(name="a", uid="a"), CallBot(name="k", uid="k")], max_hands=3
        )
        reference.start()
        self.assertEqual(_comparable(loaded.state), _comparable(reference.state))

    def test_eliminated_players_need_not_be_supplied(self):
        players = [AggressiveBot(name=n, uid=n) for n in ("a", "b", "c")]
        game = _new_game(players, stack=20, max_hands=100, save_dir=self.dir / "s")
        game.start()
        alive = [p.uid for p in game.state.get_non_eliminated_players()]
        self.assertEqual(len(alive), 1)

        loaded = Game.load(
            self.dir / "s",
            players=[AggressiveBot(name=uid, uid=uid) for uid in alive],
            log_events=False,
        )
        loaded.start()
        self.assertEqual(loaded.state.stage, GameStage.GAME_OVER)


class TestCrash(SaveTestCase):
    def test_killed_process_resumes_from_last_completed_hand(self):
        save_dir = self.dir / "crashed"
        script = textwrap.dedent(
            f"""
            import sys
            sys.path.insert(0, {str(TESTS_DIR)!r})
            from test_savegame import KillerBot, _new_game
            from maverick.players import CallBot
            game = _new_game(
                [CallBot(name="a", uid="a"), KillerBot(4, name="k", uid="k")],
                max_hands=8,
                save_dir={str(save_dir)!r},
            )
            game.start()
            """
        )
        result = subprocess.run(  # nosec B603 - fixed arguments
            [sys.executable, "-c", script], capture_output=True, timeout=120
        )
        self.assertEqual(result.returncode, 17, result.stderr.decode())

        loaded = Game.load(
            save_dir,
            players=[CallBot(name="a", uid="a"), CallBot(name="k", uid="k")],
            log_events=False,
        )
        self.assertEqual(loaded.state.hand_number, 3)
        self.assertEqual(loaded.state.stage, GameStage.HAND_COMPLETE)
        loaded.start()

        reference = _new_game(
            [CallBot(name="a", uid="a"), CallBot(name="k", uid="k")],
            max_hands=8,
            save_dir=self.dir / "reference",
        )
        reference.start()
        self.assertEqual(_comparable(loaded.state), _comparable(reference.state))
        self.assertEqual(
            _dealt_cards(Replay(save_dir)), _dealt_cards(Replay(self.dir / "reference"))
        )

    def test_events_after_the_checkpoint_are_dropped_on_load(self):
        save_dir = self.dir / "s"
        _new_game(_players(), max_hands=2, save_dir=save_dir).start()
        checkpoint = json.loads((save_dir / CHECKPOINT_FILE).read_text())
        log = save_dir / EVENTS_FILE
        complete_line = log.read_text().splitlines(keepends=True)[-1]
        with log.open("a") as handle:
            handle.write(complete_line)
            handle.write('{"event": {"type": 3')  # cut off by a crash

        # A replay reads complete lines only
        self.assertEqual(len(Replay(save_dir)), checkpoint["events"] + 2)

        Game.load(save_dir, players=_players(), log_events=False)
        self.assertEqual(log.stat().st_size, checkpoint["log_size"])
        self.assertEqual(len(Replay(save_dir)), checkpoint["events"])


class TestReplay(SaveTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.game = _new_game(_players(), max_hands=4, save_dir=self.dir / "s")
        self.game.start()

    def test_replay_creates_no_players(self):
        with mock.patch.object(Player, "__init__", side_effect=AssertionError):
            replay = Replay(self.dir / "s")
            steps = list(replay)
        self.assertEqual(len(steps), len(replay))
        self.assertEqual(_comparable(steps[-1][1]), _comparable(self.game.state))

    def test_replay_matches_the_history(self):
        replay = Replay(self.dir / "s")
        expected = [e for e in self.game.history]
        self.assertEqual(list(replay.events), expected)
        self.assertEqual(replay.hand_numbers, [1, 2, 3, 4])
        self.assertEqual(replay.game_uid, self.game.uid)
        self.assertEqual(replay.seed, self.game.seed)
        self.assertEqual(replay.rules, self.game.rules)
        self.assertEqual(replay.header.format_version, SAVE_FORMAT_VERSION)
        self.assertEqual(
            [(p.uid, p.name, p.seat) for p in replay.players],
            [
                ("u-counter", "counter", 0),
                ("u-caller", "caller", 1),
                ("u-aggressor", "aggressor", 2),
            ],
        )

    def test_states_show_every_holding(self):
        replay = Replay(self.dir / "s")
        replay.go_to_hand(2)
        while replay.event.type != GameEventType.HOLE_CARDS_DEALT:
            self.assertTrue(replay.forward())
        holdings = [p.state.holding for p in replay.state.players]
        self.assertTrue(all(h is not None and len(h.cards) == 2 for h in holdings))

    def test_cursor(self):
        replay = Replay(self.dir / "s")
        self.assertEqual(replay.position, 0)
        self.assertEqual(replay.event.type, GameEventType.PLAYER_JOINED)
        self.assertFalse(replay.backward())
        self.assertTrue(replay.forward(3))
        self.assertEqual(replay.position, 3)
        self.assertTrue(replay.backward(2))
        self.assertEqual(replay.position, 1)

        last = replay.seek(-1)
        self.assertEqual(last.type, GameEventType.GAME_ENDED)
        self.assertEqual(replay.position, len(replay) - 1)
        self.assertFalse(replay.forward())
        self.assertEqual(replay.state.stage, GameStage.GAME_OVER)

        event = replay.go_to_hand(3)
        self.assertEqual(
            (event.type, event.hand_number), (GameEventType.HAND_STARTED, 3)
        )
        self.assertEqual(replay.event, event)

        with self.assertRaises(IndexError):
            replay.seek(len(replay))
        with self.assertRaises(IndexError):
            replay.state_at(-1)
        with self.assertRaises(KeyError):
            replay.go_to_hand(99)

    def test_hand(self):
        replay = Replay(self.dir / "s")
        steps = replay.hand(2)
        self.assertEqual(steps[0][0].type, GameEventType.HAND_STARTED)
        self.assertEqual(steps[-1][0].type, GameEventType.HAND_ENDED)
        self.assertTrue(all(e.hand_number == 2 for e, _ in steps))
        self.assertEqual(replay.position, 0)
        with self.assertRaises(KeyError):
            replay.hand(99)

    def test_empty_log(self):
        (self.dir / "s" / EVENTS_FILE).write_text("")
        replay = Replay(self.dir / "s")
        self.assertEqual(len(replay), 0)
        self.assertFalse(replay.forward())
        with self.assertRaises(IndexError):
            _ = replay.event


class TestSaveFormat(SaveTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.save_dir = self.dir / "s"
        _new_game(_players(), max_hands=2, save_dir=self.save_dir).start()

    def _edit_json(self, name: str, change) -> None:
        path = self.save_dir / name
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def _load(self):
        return Game.load(self.save_dir, players=_players(), log_events=False)

    def test_files_are_json_only(self):
        for name in (HEADER_FILE, CHECKPOINT_FILE):
            raw = (self.save_dir / name).read_bytes()
            self.assertNotIn(b"\x80", raw)  # pickle protocol marker
            self.assertIsInstance(json.loads(raw), dict)
        lines = (self.save_dir / EVENTS_FILE).read_text().splitlines()
        self.assertTrue(lines)
        for line in lines:
            self.assertEqual(set(json.loads(line)), {"event", "state"})

    def test_loading_unpickles_nothing_and_imports_nothing(self):
        forbidden = mock.Mock(side_effect=AssertionError("must not be called"))
        with (
            mock.patch("pickle.loads", forbidden),
            mock.patch("pickle.load", forbidden),
            mock.patch("importlib.import_module", forbidden),
        ):
            game = self._load()
            Replay(self.save_dir)
        forbidden.assert_not_called()
        game.close()

    def test_code_references_in_the_save_are_rejected(self):
        self._edit_json(HEADER_FILE, lambda d: d.update(player_class="os.system"))
        with self.assertRaisesRegex(SaveFormatError, "header"):
            self._load()

    def test_unsupported_version_fails_clearly(self):
        self._edit_json(HEADER_FILE, lambda d: d.update(format_version=99))
        with self.assertRaisesRegex(SaveFormatError, "version 99"):
            self._load()
        with self.assertRaisesRegex(SaveFormatError, "version 99"):
            Replay(self.save_dir)

    def test_unsupported_checkpoint_version_fails_clearly(self):
        self._edit_json(CHECKPOINT_FILE, lambda d: d.update(format_version=2))
        with self.assertRaisesRegex(SaveFormatError, "checkpoint .*version 2"):
            self._load()

    def test_missing_and_malformed_files(self):
        (self.save_dir / CHECKPOINT_FILE).write_text("{not json")
        with self.assertRaisesRegex(SaveFormatError, "not valid JSON"):
            self._load()
        (self.save_dir / CHECKPOINT_FILE).unlink()
        with self.assertRaisesRegex(SaveFormatError, "doesn't exist"):
            self._load()
        (self.save_dir / HEADER_FILE).write_text("[1, 2]")
        with self.assertRaisesRegex(SaveFormatError, "not a JSON object"):
            Replay(self.save_dir)
        with self.assertRaisesRegex(SaveFormatError, "doesn't exist"):
            Replay(self.dir / "nothing here")

    def test_malformed_event_log(self):
        log = self.save_dir / EVENTS_FILE
        lines = log.read_text().splitlines(keepends=True)
        log.write_text("".join(lines[:2]) + "[]\n")
        with self.assertRaisesRegex(SaveFormatError, "Line 3 .* malformed"):
            Replay(self.save_dir)
        log.write_text("".join(lines[:2]) + "{oops\n")
        with self.assertRaisesRegex(SaveFormatError, "Line 3 .* not valid JSON"):
            Replay(self.save_dir)
        log.write_text('{"event": {"type": "nope"}, "state": {}}\n')
        with self.assertRaisesRegex(SaveFormatError, "Line 1 .* invalid event"):
            Replay(self.save_dir)
        bad_state = json.loads(lines[0])
        bad_state["state"] = {"pot": "lots"}
        log.write_text(json.dumps(bad_state) + "\n")
        with self.assertRaisesRegex(SaveFormatError, "Line 1 .* invalid state"):
            Replay(self.save_dir).state_at(0)
        log.write_text("".join(lines[:2]))
        with self.assertRaisesRegex(SaveFormatError, "expects"):
            self._load()
        log.unlink()
        with self.assertRaisesRegex(SaveFormatError, "doesn't exist"):
            Replay(self.save_dir)

    def test_event_log_shorter_than_the_checkpoint(self):
        self._edit_json(CHECKPOINT_FILE, lambda d: d.update(log_size=10**9))
        with self.assertRaisesRegex(SaveFormatError, "shorter"):
            self._load()

    def test_inconsistent_checkpoints(self):
        cases = {
            "another game": lambda d: d.update(game_uid="other"),
            "random state": lambda d: d.update(rng_state=[3, [1, 2], None]),
            "between two hands": lambda d: d["state"].update(stage=6),
            "seats": lambda d: d["table"].update(seats=[None] * 3),
            "button": lambda d: d["table"].update(button_seat=42),
            "don't match": lambda d: d["table"]["seats"].__setitem__(0, "ghost"),
            "checkpoint is invalid": lambda d: d.pop("table"),
        }
        original = (self.save_dir / CHECKPOINT_FILE).read_text()
        for message, change in cases.items():
            with self.subTest(message):
                (self.save_dir / CHECKPOINT_FILE).write_text(original)
                self._edit_json(CHECKPOINT_FILE, change)
                with self.assertRaisesRegex(SaveFormatError, message):
                    self._load()

    def test_rules_survive_json(self):
        rules = PokerRules(
            dealing=DealingRules(),
            stakes=StakesRules(small_blind=1, big_blind=2),
            showdown=ShowdownRules(),
        )
        self.assertEqual(PokerRules.model_validate_json(rules.model_dump_json()), rules)
        with self.assertRaises(ValidationError):
            DealingRules(board_deal_pattern=[0, 3, 1, 1])

    @unittest.skipIf(os.name != "posix", "file modes are POSIX only")
    def test_files_are_private(self):
        self.assertEqual(self.save_dir.stat().st_mode & 0o777, 0o700)
        for name in (HEADER_FILE, EVENTS_FILE, CHECKPOINT_FILE):
            self.assertEqual((self.save_dir / name).stat().st_mode & 0o777, 0o600)


class TestValidation(SaveTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.save_dir = self.dir / "s"
        _new_game(_players(), max_hands=1, save_dir=self.save_dir).start()

    def test_existing_save_is_not_overwritten(self):
        with self.assertRaisesRegex(FileExistsError, "Game.load"):
            Game(small_blind=1, big_blind=2, save_dir=self.save_dir)

    def test_save_created_after_the_game_is_detected(self):
        other = self.dir / "other"
        game = _new_game(_players(), max_hands=1, save_dir=other)
        other.mkdir()
        (other / HEADER_FILE).write_text("{}")
        with self.assertRaises(FileExistsError):
            game.start()

    def test_players_must_match_the_table(self):
        cases = {
            "missing: aggressor": _players()[:2],
            "not: stranger": [*_players(), CallBot(name="stranger")],
            "supplied twice": [*_players(), CallBot(name="x", uid="u-caller")],
            "called 'caller'": [
                *_players()[:1],
                CallBot(name="renamed", uid="u-caller"),
                *_players()[2:],
            ],
        }
        for message, players in cases.items():
            with self.subTest(message):
                with self.assertRaisesRegex(ValueError, message):
                    Game.load(self.save_dir, players=players, log_events=False)

    def test_failed_import_stops_loading_and_workers(self):
        class NoImport(CallBot):
            register = False
            import_state = None

        self._replace_player_state("u-caller", {"x": 1})
        players = [
            *_players()[:1],
            NoImport(name="caller", uid="u-caller"),
            _players()[2],
        ]
        with self.assertRaises(TypeError):
            Game.load(self.save_dir, players=players, log_events=False)

    def _replace_player_state(self, uid: str, state) -> None:
        path = self.save_dir / CHECKPOINT_FILE
        data = json.loads(path.read_text())
        data["players"][uid] = {"state": state, "export_failed": False}
        path.write_text(json.dumps(data))


class TestFailedExports(SaveTestCase):
    def _play(self, bot, isolation: str = "none") -> Path:
        save_dir = self.dir / isolation
        game = _new_game(
            [bot, CallBot(name="b", uid="b")],
            max_hands=2,
            save_dir=save_dir,
            player_isolation=isolation,
        )
        with self.assertLogs("maverick", logging.WARNING) as logs:
            game.start()
        self.assertTrue(any("Could not save the state" in m for m in logs.output))
        self.assertEqual(game.state.stage, GameStage.GAME_OVER)
        return save_dir

    def _check_restored_fresh(self, save_dir: Path, uid: str) -> None:
        checkpoint = json.loads((save_dir / CHECKPOINT_FILE).read_text())
        self.assertEqual(
            checkpoint["players"][uid], {"state": None, "export_failed": True}
        )
        with self.assertLogs("maverick", logging.WARNING) as logs:
            Game.load(
                save_dir,
                players=[CallBot(name="x", uid=uid), CallBot(name="b", uid="b")],
                log_events=False,
            ).close()
        self.assertTrue(any("continues without it" in m for m in logs.output))

    def test_failed_export_in_process(self):
        save_dir = self._play(FailingExportBot(name="x", uid="x"))
        self._check_restored_fresh(save_dir, "x")

    def test_export_that_is_not_a_dict(self):
        save_dir = self._play(WrongExportBot(name="x", uid="x"))
        self._check_restored_fresh(save_dir, "x")

    def test_failed_export_isolated(self):
        save_dir = self._play(FailingExportBot(name="x", uid="x"), "process")
        self._check_restored_fresh(save_dir, "x")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
