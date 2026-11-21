"""Tests for seeding the random number generators of isolated players."""

import random
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from maverick import (
    ActionType,
    Game,
    GameEventType,
    Player,
    PlayerAction,
    PlayerState,
)
from maverick._isolation import derive_player_seed
from maverick._isolation.worker import seed_random


class RandomBot(Player):
    """Folds, checks, calls or raises at random, and remembers what it drew."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draws: list[float] = []

    def on_hand_started(self, event, game) -> None:
        self.draws.append(random.random())  # nosec B311

    def decide_action(
        self, *, valid_actions, min_raise_amount, call_amount, **_
    ) -> PlayerAction:
        r = self._draw()
        self.draws.append(r)
        if r < 0.2 and ActionType.FOLD in valid_actions:
            action_type, amount = ActionType.FOLD, None
        elif r < 0.4 and ActionType.RAISE in valid_actions:
            action_type, amount = ActionType.RAISE, call_amount + min_raise_amount
        elif ActionType.CHECK in valid_actions:
            action_type, amount = ActionType.CHECK, None
        else:
            action_type, amount = ActionType.CALL, None
        return PlayerAction(player_uid=self.uid, action_type=action_type, amount=amount)

    def _draw(self) -> float:
        return random.random()  # nosec B311

    def export_state(self):
        return {"draws": self.draws}

    def import_state(self, state):
        self.draws = list(state["draws"])


class MoodyBot(RandomBot):
    """Draws its next decision when the button moves, between two hands.

    The button moves after the checkpoint of a hand has been written, so a resumed
    game must reseed the bot before that.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next_draw: float | None = None

    def on_game_state_changed(self, event, game) -> None:
        before, after = event.payload["before"], event.payload["after"]
        if before["button_position"] != after["button_position"]:
            self.next_draw = random.random()  # nosec B311

    def _draw(self) -> float:
        if self.next_draw is None:
            return super()._draw()
        draw, self.next_draw = self.next_draw, None
        return draw


def _players(cls: type[RandomBot] = RandomBot) -> list[RandomBot]:
    return [cls(name=n, uid=n) for n in ("a", "b", "c")]


def _new_game(seed: int, cls: type[RandomBot] = RandomBot, **kwargs) -> Game:
    kwargs.setdefault("max_hands", 6)
    game = Game(
        small_blind=1,
        big_blind=2,
        log_events=False,
        player_isolation="process",
        seed=seed,
        **kwargs,
    )
    for player in _players(cls):
        game.add_player(player, state=PlayerState(stack=1000))
    return game


def _record_actions(game: Game) -> list[tuple]:
    actions: list[tuple] = []

    def record(event, _game) -> None:
        actions.append(
            (
                event.hand_number,
                event.player_uid,
                event.action.action_type.name,
                event.action.amount,
            )
        )

    game.subscribe(GameEventType.PLAYER_ACTION_TAKEN, record)
    # Without a listener, GAME_STATE_CHANGED is not emitted, not even to players
    game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda event, game: None)
    return actions


def _play(seed: int, cls: type[RandomBot] = RandomBot) -> tuple[list[tuple], dict]:
    """Play a game and return its actions and what each bot drew."""
    with _new_game(seed, cls) as game:
        actions = _record_actions(game)
        game.start()
    draws = {uid: game.get_player_state(uid)["draws"] for uid in ("a", "b", "c")}
    return actions, draws


class TestIsolatedGames(unittest.TestCase):
    def test_same_seed_gives_the_same_decisions(self):
        first_actions, first_draws = _play(7)
        self.assertGreater(len(first_actions), 10)
        # the bots folded, checked, called and raised
        self.assertGreaterEqual(len({a[2] for a in first_actions}), 3)
        second_actions, second_draws = _play(7)
        self.assertEqual(first_actions, second_actions)
        self.assertEqual(first_draws, second_draws)

    def test_different_seed_gives_different_decisions(self):
        _, first_draws = _play(7)
        _, second_draws = _play(8)
        self.assertNotEqual(first_draws["a"], second_draws["a"])

    def test_players_draw_different_numbers(self):
        _, draws = _play(7)
        self.assertNotEqual(draws["a"][:3], draws["b"][:3])

    def test_resumed_game_makes_the_same_decisions(self):
        self.check_resume(RandomBot)

    def test_resumed_game_with_draws_between_hands(self):
        self.check_resume(MoodyBot)

    def check_resume(self, cls: type[RandomBot]) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with _new_game(7, cls, max_hands=3, save_dir=Path(tmp) / "s") as first:
                _record_actions(first)  # same listeners as in the other games
                first.start()
            with Game.load(
                Path(tmp) / "s",
                players=_players(cls),
                max_hands=6,
                log_events=False,
                player_isolation="process",
            ) as resumed:
                resumed_actions = _record_actions(resumed)
                resumed.start()

        through_actions, _ = _play(7, cls)
        self.assertTrue(resumed_actions)
        self.assertEqual(resumed_actions, [a for a in through_actions if a[0] > 3])


class TestDerivePlayerSeed(unittest.TestCase):
    def test_is_stable_across_interpreters(self):
        # hash() is randomized per interpreter, the derivation must not be
        self.assertEqual(derive_player_seed(1, "a", 0), 0x266441E3275A1E82)

    def test_depends_on_every_input(self):
        base = derive_player_seed(1, "a", 1)
        self.assertNotEqual(base, derive_player_seed(2, "a", 1))
        self.assertNotEqual(base, derive_player_seed(1, "b", 1))
        self.assertNotEqual(base, derive_player_seed(1, "a", 2))

    def test_fits_in_64_bits(self):
        for hand in range(100):
            self.assertTrue(0 <= derive_player_seed(-5, "x", hand) < 2**64)


class TestSeedRandom(unittest.TestCase):
    def setUp(self) -> None:
        state = random.getstate()
        self.addCleanup(random.setstate, state)

    def test_seeds_the_random_module(self):
        seed_random(3)
        first = random.random()  # nosec B311
        seed_random(3)
        self.assertEqual(first, random.random())  # nosec B311

    def test_seeds_numpy_only_if_imported(self):
        fake = types.SimpleNamespace(random=mock.Mock())
        with mock.patch.dict(sys.modules, {"numpy": fake}):
            seed_random(2**64 - 1)
        fake.random.seed.assert_called_once_with(2**32 - 1)
        with mock.patch.dict(sys.modules, {"numpy": None}):
            seed_random(1)  # no numpy, nothing to seed

    def test_a_broken_numpy_is_ignored(self):
        fake = types.SimpleNamespace(random=mock.Mock())
        fake.random.seed.side_effect = RuntimeError("broken")
        with mock.patch.dict(sys.modules, {"numpy": fake}):
            seed_random(1)


if __name__ == "__main__":
    unittest.main()
