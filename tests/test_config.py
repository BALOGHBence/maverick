"""Tests for resolving the isolation settings from code, environment and pyproject."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from maverick import Game, PlayerIsolation
from maverick.config import IsolationSettings, _clear_config_cache, resolve_settings


class ConfigTestCase(unittest.TestCase):
    """Runs every test in an empty temporary directory without maverick env vars."""

    def setUp(self) -> None:
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name).resolve()
        os.chdir(self.dir)
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("MAVERICK_PLAYER_ISOLATION", "MAVERICK_DECISION_TIMEOUT")
        }
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()
        _clear_config_cache()

    def tearDown(self) -> None:
        self._env.stop()
        os.chdir(self._cwd)
        self._tmp.cleanup()
        _clear_config_cache()

    def write_pyproject(self, body: str, directory: Path | None = None) -> None:
        (directory or self.dir).joinpath("pyproject.toml").write_text(body)


class TestDefaults(ConfigTestCase):
    def test_defaults_without_any_source(self):
        settings = resolve_settings()
        self.assertEqual(settings.player_isolation, PlayerIsolation.NONE)
        self.assertIsNone(settings.decision_timeout)

    def test_pyproject_without_maverick_table(self):
        self.write_pyproject('[project]\nname = "x"\n')
        self.assertEqual(resolve_settings(), IsolationSettings())

    def test_game_uses_defaults(self):
        game = Game(small_blind=1, big_blind=2)
        self.assertEqual(game.settings, IsolationSettings())


class TestPrecedence(ConfigTestCase):
    def test_pyproject(self):
        self.write_pyproject(
            '[tool.maverick]\nplayer_isolation = "process"\ndecision_timeout = 2.5\n'
        )
        settings = resolve_settings()
        self.assertEqual(settings.player_isolation, PlayerIsolation.PROCESS)
        self.assertEqual(settings.decision_timeout, 2.5)

    def test_pyproject_found_in_parent_directory(self):
        self.write_pyproject('[tool.maverick]\nplayer_isolation = "process"\n')
        child = self.dir / "a" / "b"
        child.mkdir(parents=True)
        os.chdir(child)
        self.assertEqual(resolve_settings().player_isolation, PlayerIsolation.PROCESS)

    def test_env_overrides_pyproject(self):
        self.write_pyproject(
            '[tool.maverick]\nplayer_isolation = "process"\ndecision_timeout = 2.5\n'
        )
        os.environ["MAVERICK_PLAYER_ISOLATION"] = "none"
        os.environ["MAVERICK_DECISION_TIMEOUT"] = "7"
        settings = resolve_settings()
        self.assertEqual(settings.player_isolation, PlayerIsolation.NONE)
        self.assertEqual(settings.decision_timeout, 7.0)

    def test_empty_env_var_is_ignored(self):
        self.write_pyproject('[tool.maverick]\nplayer_isolation = "process"\n')
        os.environ["MAVERICK_PLAYER_ISOLATION"] = " "
        self.assertEqual(resolve_settings().player_isolation, PlayerIsolation.PROCESS)

    def test_argument_overrides_env_and_pyproject(self):
        self.write_pyproject("[tool.maverick]\ndecision_timeout = 2.5\n")
        os.environ["MAVERICK_PLAYER_ISOLATION"] = "process"
        os.environ["MAVERICK_DECISION_TIMEOUT"] = "7"
        settings = resolve_settings(
            player_isolation=PlayerIsolation.NONE, decision_timeout=1
        )
        self.assertEqual(settings.player_isolation, PlayerIsolation.NONE)
        self.assertEqual(settings.decision_timeout, 1.0)

    def test_sources_are_resolved_per_field(self):
        self.write_pyproject("[tool.maverick]\ndecision_timeout = 2.5\n")
        os.environ["MAVERICK_PLAYER_ISOLATION"] = "process"
        settings = resolve_settings()
        self.assertEqual(settings.player_isolation, PlayerIsolation.PROCESS)
        self.assertEqual(settings.decision_timeout, 2.5)

    def test_game_arguments(self):
        os.environ["MAVERICK_PLAYER_ISOLATION"] = "process"
        game = Game(
            small_blind=1, big_blind=2, player_isolation="none", decision_timeout=3
        )
        self.assertEqual(game.settings.player_isolation, PlayerIsolation.NONE)
        self.assertEqual(game.settings.decision_timeout, 3.0)


class TestInvalidValues(ConfigTestCase):
    def test_invalid_env_value_names_the_variable(self):
        os.environ["MAVERICK_PLAYER_ISOLATION"] = "thread"
        with self.assertRaisesRegex(ValueError, "MAVERICK_PLAYER_ISOLATION"):
            resolve_settings()

    def test_invalid_env_timeout(self):
        os.environ["MAVERICK_DECISION_TIMEOUT"] = "soon"
        with self.assertRaisesRegex(ValueError, "MAVERICK_DECISION_TIMEOUT"):
            resolve_settings()

    def test_non_positive_timeout(self):
        with self.assertRaisesRegex(ValueError, "decision_timeout from argument"):
            resolve_settings(decision_timeout=0)

    def test_invalid_pyproject_value_names_the_file(self):
        self.write_pyproject('[tool.maverick]\nplayer_isolation = "thread"\n')
        with self.assertRaisesRegex(ValueError, r"\[tool.maverick\] in .*pyproject"):
            resolve_settings()

    def test_unknown_pyproject_key(self):
        self.write_pyproject('[tool.maverick]\nplayer_isolaton = "process"\n')
        with self.assertRaisesRegex(ValueError, "player_isolaton"):
            resolve_settings()

    def test_maverick_section_must_be_a_table(self):
        self.write_pyproject('[tool]\nmaverick = "process"\n')
        with self.assertRaisesRegex(ValueError, "must be a table"):
            resolve_settings()

    def test_invalid_game_argument(self):
        with self.assertRaises(ValueError):
            Game(small_blind=1, big_blind=2, player_isolation="thread")


if __name__ == "__main__":
    unittest.main()
