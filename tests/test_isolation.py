"""Tests for running players in worker processes (``player_isolation="process"``)."""

import gc
import json
import os
import random
import sys
import tempfile
import time
import unittest
import warnings
from pathlib import Path

from maverick import (
    ActionType,
    Deck,
    Game,
    GameEventType,
    GameStage,
    Player,
    PlayerAction,
    PlayerState,
)
from maverick import players as builtin_players
from maverick._isolation import PlayerFailure, ProcessPlayer
from maverick._isolation.worker import ViewDelta, run_worker
from maverick.players import CallBot


def _check_or_call(player: Player, valid_actions) -> PlayerAction:
    action_type = (
        ActionType.CHECK if ActionType.CHECK in valid_actions else ActionType.CALL
    )
    return PlayerAction(player_uid=player.uid, action_type=action_type)


class CheaterBot(Player):
    """The proof of concept from issue #101: looks for the engine by introspection."""

    def __init__(self, report_path: str, **kwargs):
        super().__init__(**kwargs)
        self.report_path = report_path

    def decide_action(self, *, game, valid_actions, **_) -> PlayerAction:
        findings = []
        frame = sys._getframe(1)
        while frame is not None:
            if isinstance(frame.f_locals.get("self"), Game):
                findings.append("game via stack")
            frame = frame.f_back
        for obj in gc.get_objects():
            if isinstance(obj, Game):
                findings.append("game via gc")
                opponents = [
                    s.state.holding for s in obj.state.players if s.uid != self.uid
                ]
                if any(h is not None for h in opponents):
                    findings.append("opponent holdings")
            elif isinstance(obj, Deck) and obj.cards:
                findings.append("deck via gc")
        with open(self.report_path, "a") as f:
            f.write(json.dumps(sorted(set(findings))) + "\n")
        return _check_or_call(self, valid_actions)


class RecorderBot(Player):
    """Records the hooks it receives and writes them to a file when the game ends."""

    def __init__(self, report_path: str, **kwargs):
        super().__init__(**kwargs)
        self.report_path = report_path
        self.calls: list[list] = []

    def decide_action(self, *, game, valid_actions, **_) -> PlayerAction:
        self.calls.append(["decide", len(game.history), game.holding is not None])
        return _check_or_call(self, valid_actions)

    def on_event(self, event, game) -> None:
        self.calls.append(["on_event", event.type.name, len(game.history)])

    def on_hand_started(self, event, game) -> None:
        self.calls.append(["on_hand_started", game.state.hand_number])

    def on_game_ended(self, event, game) -> None:
        self.calls.append(["on_game_ended"])
        Path(self.report_path).write_text(json.dumps(self.calls))

    def export_state(self) -> dict:
        return {"calls": len(self.calls)}


class StatefulBot(CallBot):
    """Counts its decisions and reports the count through export_state."""

    register = False

    def __init__(self, mode: str = "ok", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.decisions = 0

    def decide_action(self, **kwargs) -> PlayerAction:
        self.decisions += 1
        return super().decide_action(**kwargs)

    def export_state(self):
        if self.mode == "raise":
            raise RuntimeError("export boom")
        if self.mode == "not json":
            return {"decisions": {self.decisions}}
        if self.mode == "not a dict":
            return [self.decisions]
        return {"decisions": self.decisions}


class SlowBot(Player):
    """Takes too long for its first decision only."""

    def __init__(self, delay: float, **kwargs):
        super().__init__(**kwargs)
        self.delay = delay
        self.decisions = 0

    def decide_action(self, *, game, valid_actions, **_) -> PlayerAction:
        self.decisions += 1
        if self.decisions == 1:
            time.sleep(self.delay)
        return _check_or_call(self, valid_actions)


class RaisingBot(Player):
    def decide_action(self, **_) -> PlayerAction:
        raise RuntimeError("boom")


class DyingBot(Player):
    def decide_action(self, **_) -> PlayerAction:
        os._exit(1)


class WrongTypeBot(Player):
    def decide_action(self, **_) -> PlayerAction:
        return "fold"  # type: ignore[return-value]


class NegativeAmountBot(Player):
    """Returns an action that fails validation in the engine."""

    def decide_action(self, **_) -> PlayerAction:
        return PlayerAction.model_construct(
            player_uid=self.uid, action_type=ActionType.BET, amount=-5
        )


class FailingHookBot(CallBot):
    register = False  # don't replace CallBot in the cls_uid registry

    def on_hand_started(self, event, game) -> None:
        raise RuntimeError("hook boom")


def _fail_to_load():
    raise RuntimeError("can't load me")


class UnloadableBot(CallBot):
    """Pickles fine, but can't be unpickled in the worker."""

    register = False

    def __reduce__(self):
        return (_fail_to_load, ())


def _make_game(*players: Player, isolation: str = "process", **kwargs) -> Game:
    kwargs.setdefault("max_hands", 3)
    game = Game(
        small_blind=1,
        big_blind=2,
        log_events=False,
        player_isolation=isolation,
        **kwargs,
    )
    for player in players:
        game.add_player(player, state=PlayerState(stack=200))
    return game


class IsolationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class TestProofOfConcept(IsolationTestCase):
    def _findings(self, isolation: str) -> set[str]:
        report = self.dir / f"{isolation}.jsonl"
        with _make_game(
            CheaterBot(str(report), name="cheater"),
            CallBot(name="victim"),
            isolation=isolation,
        ) as game:
            game.start()
        lines = report.read_text().splitlines()
        self.assertTrue(lines)
        return set().union(*(json.loads(line) for line in lines))

    def test_cheater_reaches_the_engine_in_process(self):
        findings = self._findings("none")
        self.assertIn("game via stack", findings)
        self.assertIn("game via gc", findings)
        self.assertIn("opponent holdings", findings)

    def test_cheater_finds_nothing_in_isolated_mode(self):
        self.assertEqual(self._findings("process"), set())


class TestBuiltinBots(IsolationTestCase):
    def test_all_builtin_bots_play_in_isolated_mode(self):
        classes = [getattr(builtin_players, name) for name in builtin_players.__all__]
        for start in range(0, len(classes), 6):
            batch = classes[start : start + 6]
            with self.subTest(bots=[c.__name__ for c in batch]):
                game = _make_game(*(cls(name=cls.__name__) for cls in batch))
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    game.start()
                self.assertEqual(game.state.stage, GameStage.GAME_OVER)
                self.assertFalse(
                    [w for w in caught if "failed to decide" in str(w.message)]
                )


class TestHooks(IsolationTestCase):
    def _calls(self, isolation: str) -> list:
        report = self.dir / f"{isolation}.json"
        random.seed(1234)
        game = _make_game(
            RecorderBot(str(report), name="recorder"),
            CallBot(name="caller"),
            isolation=isolation,
            first_button_position=0,
        )
        game.start()
        return json.loads(report.read_text())

    def test_hooks_match_in_process_mode(self):
        in_process = self._calls("none")
        isolated = self._calls("process")
        self.assertIn(["on_game_ended"], isolated)
        self.assertTrue(any(c[0] == "decide" for c in isolated))
        self.assertEqual(in_process, isolated)

    def test_hook_exceptions_are_logged(self):
        game = _make_game(FailingHookBot(name="a"), CallBot(name="b"))
        with self.assertLogs("maverick", level="WARNING") as logs:
            game.start()
        self.assertTrue(
            any(
                "on_hand_started hook" in line and "hook boom" in line
                for line in logs.output
            )
        )
        self.assertEqual(game.state.stage, GameStage.GAME_OVER)

    def test_parent_side_player_view_is_updated(self):
        bot = CallBot(name="a")
        game = _make_game(bot, CallBot(name="b"))
        game.start()
        self.assertIsNotNone(bot.game)
        self.assertEqual(bot.game.player_uid, bot.uid)


class TestFailures(IsolationTestCase):
    def _play(self, bot: Player, **kwargs) -> Game:
        game = _make_game(bot, CallBot(name="caller"), **kwargs)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            game.start()
        self.assertEqual(game.state.stage, GameStage.GAME_OVER)
        self.assertTrue(
            any("folding" in str(w.message) for w in caught),
            "the failing player should have folded",
        )
        return game

    def _folds(self, game: Game, uid: str) -> int:
        return sum(
            1
            for e in game.history
            if e.action is not None
            and e.player_uid == uid
            and e.action.action_type == ActionType.FOLD
        )

    def test_timeout_folds_and_late_reply_is_ignored(self):
        # The late reply to the first decision arrives while the engine waits for
        # the second one, which must still get its own answer in time.
        bot = SlowBot(delay=0.7, name="slow")
        game = self._play(bot, decision_timeout=0.5)
        self.assertEqual(self._folds(game, bot.uid), 1)

    def test_exception_folds(self):
        bot = RaisingBot(name="raiser")
        game = self._play(bot)
        self.assertEqual(self._folds(game, bot.uid), 3)

    def test_dead_worker_folds_for_the_rest_of_the_game(self):
        bot = DyingBot(name="dying")
        game = self._play(bot)
        self.assertEqual(self._folds(game, bot.uid), 3)

    def test_wrong_return_type_folds(self):
        self._play(WrongTypeBot(name="wrong"))

    def test_invalid_action_folds(self):
        self._play(NegativeAmountBot(name="negative"))

    def test_unpicklable_player_is_rejected(self):
        bot = CallBot(name="a")
        bot.strategy = lambda: None
        game = _make_game()
        with self.assertRaisesRegex(TypeError, "pickled"):
            game.add_player(bot, state=PlayerState(stack=200))
        self.assertEqual(game.state.players, [])
        self.assertEqual(game._proxies, {})

    def test_player_that_cant_be_loaded_is_rejected(self):
        game = _make_game()
        with self.assertRaisesRegex(RuntimeError, "can't load me"):
            game.add_player(UnloadableBot(name="a"), state=PlayerState(stack=200))
        self.assertEqual(game.state.players, [])


class TestLifecycle(IsolationTestCase):
    def test_workers_stop_when_the_game_ends(self):
        game = _make_game(CallBot(name="a"), CallBot(name="b"))
        processes = [p.process for p in game._proxies.values()]
        self.assertTrue(all(p.is_alive() for p in processes))
        game.start()
        self.assertEqual(game._proxies, {})
        self.assertFalse(any(p.is_alive() for p in processes))

    def test_remove_player_stops_its_worker(self):
        a, b, c = CallBot(name="a"), CallBot(name="b"), CallBot(name="c")
        game = _make_game(a, b, c)
        process = game._proxies[a.uid].process
        game.remove_player(a)
        self.assertNotIn(a.uid, game._proxies)
        self.assertFalse(process.is_alive())
        game.close()

    def test_context_manager_closes_workers(self):
        with _make_game(CallBot(name="a"), CallBot(name="b")) as game:
            processes = [p.process for p in game._proxies.values()]
        self.assertFalse(any(p.is_alive() for p in processes))

    def test_public_api_returns_the_original_players(self):
        a, b = CallBot(name="a"), CallBot(name="b")
        game = _make_game(a, b, first_button_position=0, max_hands=1)
        game.start()
        self.assertIn(game.button, (a, b))
        self.assertIn(game.small_blind, (a, b))
        self.assertIn(game.big_blind, (a, b))

    def test_worker_is_stopped_if_seating_fails(self):
        game = _make_game(CallBot(name="a"))
        bot = CallBot(name="b")
        with self.assertRaisesRegex(ValueError, "occupied"):
            game.add_player(bot, state=PlayerState(stack=200, seat=0))
        self.assertNotIn(bot.uid, game._proxies)
        game.close()

    def test_in_process_mode_starts_no_workers(self):
        game = _make_game(CallBot(name="a"), CallBot(name="b"), isolation="none")
        self.assertEqual(game._proxies, {})
        game.close()  # no-op


class TestProxy(IsolationTestCase):
    def test_proxy_exposes_only_implemented_hooks(self):
        proxy = ProcessPlayer(
            RecorderBot("unused", name="r"), decision_timeout=None, logger=None
        )
        self.assertTrue(callable(proxy.on_event))
        self.assertTrue(callable(proxy.on_hand_started))
        self.assertFalse(hasattr(proxy, "on_hand_ended"))
        plain = ProcessPlayer(CallBot(name="c"), decision_timeout=None, logger=None)
        self.assertFalse(hasattr(plain, "on_event"))

    def test_decide_before_start_fails(self):
        proxy = ProcessPlayer(CallBot(name="c"), decision_timeout=None, logger=None)
        with self.assertRaises(PlayerFailure):
            proxy.decide_action(game=None)
        proxy.close()  # no-op before start


class TestExportState(IsolationTestCase):
    def _play(self, bot: Player, isolation: str = "process") -> tuple[Game, list]:
        """Plays 3 hands and reads the bot's state after every hand."""
        game = _make_game(bot, CallBot(name="caller"), isolation=isolation)
        seen = []
        game.subscribe(
            GameEventType.HAND_ENDED,
            lambda event, g: seen.append(g.get_player_state(bot)),
        )
        game.start()
        return game, seen

    def test_state_during_and_after_the_game(self):
        for isolation in ("none", "process"):
            with self.subTest(isolation=isolation):
                bot = StatefulBot(name="stateful")
                game, seen = self._play(bot, isolation)
                counts = [s["decisions"] for s in seen]
                self.assertEqual(len(counts), 3)
                self.assertEqual(counts, sorted(counts))
                self.assertGreater(counts[-1], 0)
                self.assertEqual(game.get_player_state(bot), seen[-1])
                self.assertEqual(game.get_player_state(bot.uid), seen[-1])

    def test_parent_side_object_is_not_updated_in_process_mode(self):
        bot = StatefulBot(name="stateful")
        game, _ = self._play(bot)
        self.assertEqual(bot.decisions, 0)
        self.assertGreater(game.get_player_state(bot)["decisions"], 0)

    def test_result_is_a_copy(self):
        bot = StatefulBot(name="stateful")
        game, _ = self._play(bot, isolation="none")
        game.get_player_state(bot)["decisions"] = -1
        self.assertNotEqual(game.get_player_state(bot)["decisions"], -1)

    def test_player_without_export_state(self):
        for isolation in ("none", "process"):
            with self.subTest(isolation=isolation):
                bot = CallBot(name="plain")
                game, seen = self._play(bot, isolation)
                self.assertEqual(seen, [None, None, None])
                self.assertIsNone(game.get_player_state(bot))

    def test_failing_export_returns_none_in_process_mode(self):
        for mode in ("raise", "not json", "not a dict"):
            with self.subTest(mode=mode):
                bot = StatefulBot(mode=mode, name="stateful")
                with self.assertLogs("maverick", level="WARNING") as logs:
                    game, seen = self._play(bot)
                self.assertEqual(seen, [None, None, None])
                self.assertIsNone(game.get_player_state(bot))
                self.assertTrue(any("state of player" in l for l in logs.output))
                self.assertEqual(game.state.stage, GameStage.GAME_OVER)

    def test_failing_export_raises_in_process(self):
        for mode, error in (
            ("raise", RuntimeError),
            ("not json", TypeError),
            ("not a dict", TypeError),
        ):
            with self.subTest(mode=mode):
                bot = StatefulBot(mode=mode, name="stateful")
                game = _make_game(bot, CallBot(name="caller"), isolation="none")
                with self.assertRaises(error):
                    game.get_player_state(bot)

    def test_state_is_kept_after_remove_player(self):
        bot = StatefulBot(name="stateful")
        game = _make_game(bot, CallBot(name="b"), CallBot(name="c"))
        game.remove_player(bot)
        self.assertEqual(game.get_player_state(bot), {"decisions": 0})
        game.close()

    def test_dead_worker_has_no_state(self):
        bot = DyingBot(name="dying")
        game = _make_game(bot, CallBot(name="caller"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            game.start()
        self.assertIsNone(game.get_player_state(bot))

    def test_unknown_player(self):
        game = _make_game(CallBot(name="a"), isolation="none")
        with self.assertRaises(ValueError):
            game.get_player_state("nobody")


class TestWorkerLoop(IsolationTestCase):
    """Runs the worker loop in a thread, where coverage can see it."""

    def setUp(self) -> None:
        super().setUp()
        import pickle
        import threading
        from multiprocessing import Pipe

        report = self.dir / "calls.json"
        self.bot = RecorderBot(str(report), name="r")
        self.engine, worker_conn = Pipe()
        self.thread = threading.Thread(
            target=run_worker, args=(worker_conn, pickle.dumps(self.bot))
        )
        self.thread.start()
        self.assertEqual(json.loads(self.engine.recv_bytes()), {"ready": True})
        game = _make_game(self.bot, CallBot(name="c"), isolation="none")
        self.view = game.get_player_view(self.bot.uid)

    def tearDown(self) -> None:
        self.engine.close()
        self.thread.join(5)
        super().tearDown()

    def delta(self, rules=True) -> ViewDelta:
        return ViewDelta(
            player_uid=self.view.player_uid,
            game_uid=self.view.game_uid,
            state=self.view.state,
            new_events=list(self.view.history),
            rules=self.view.rules if rules else None,
        )

    def decide(self, seq: int, rules: bool = True) -> dict:
        kwargs = dict(
            valid_actions=[ActionType.CALL],
            min_raise_amount=2,
            call_amount=1,
            min_bet_amount=2,
        )
        self.engine.send(("decide", seq, self.delta(rules), kwargs))
        return json.loads(self.engine.recv_bytes())

    def test_decide_hooks_and_close(self):
        event = self.view.history[-1]
        self.engine.send(("hook", "on_event", event, self.delta()))
        self.engine.send(("hook", "on_hand_ended", event, self.delta(False)))
        reply = self.decide(1, rules=False)
        self.assertEqual(reply["seq"], 1)
        self.assertEqual(reply["action"]["action_type"], ActionType.CALL.value)
        self.assertIsNone(reply["error"])
        # on_hand_ended doesn't exist on the bot, so the worker reports it
        self.assertEqual(len(reply["hook_errors"]), 1)
        self.assertEqual(reply["hook_errors"][0]["hook"], "on_hand_ended")
        self.engine.send(("close",))
        self.assertEqual(
            json.loads(self.engine.recv_bytes()),
            {
                "closed": True,
                "state": {"calls": 2},  # one hook and one decision
                "state_error": None,
                "hook_errors": [],
            },
        )
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())

    def test_exception_in_decide_is_reported(self):
        self.engine.send(("decide", 1, self.delta(), dict(valid_actions="not a list")))
        reply = json.loads(self.engine.recv_bytes())
        self.assertIsNone(reply["action"])
        self.assertIn("TypeError", reply["error"])

    def test_export(self):
        self.engine.send(("export", 7))
        reply = json.loads(self.engine.recv_bytes())
        self.assertEqual(reply["seq"], 7)
        self.assertEqual(reply["state"], {"calls": 0})
        self.assertIsNone(reply["state_error"])

    def test_worker_exits_when_the_engine_goes_away(self):
        self.engine.close()
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())


if __name__ == "__main__":
    unittest.main()
