"""
Library-wide settings.

Settings are resolved from the following sources, highest priority first:

1. Arguments passed explicitly in code, e.g. to :class:`~maverick.game.Game`.
2. Environment variables (``MAVERICK_PLAYER_ISOLATION``, ``MAVERICK_DECISION_TIMEOUT``).
3. The ``[tool.maverick]`` table of the nearest ``pyproject.toml``, searched from the
   current working directory upwards.
4. The defaults of :class:`IsolationSettings`.
"""

import functools
import os
import tomllib
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .enums import PlayerIsolation

__all__ = ["IsolationSettings", "resolve_settings"]

ENV_VARS: dict[str, str] = {
    "player_isolation": "MAVERICK_PLAYER_ISOLATION",
    "decision_timeout": "MAVERICK_DECISION_TIMEOUT",
}


class IsolationSettings(BaseModel):
    """Settings that control how players are isolated from the game engine.

    Fields
    ------
    player_isolation : PlayerIsolation
        Where the code of the players runs. Default is ``PlayerIsolation.NONE``, which
        runs players in the engine's process.
    decision_timeout : Optional[float]
        Maximum number of seconds an isolated player may take to decide on an action.
        A player that exceeds it folds. ``None`` (the default) means no limit. Only
        applies to isolated players.

    .. versionadded:: 0.7.0
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    player_isolation: PlayerIsolation = PlayerIsolation.NONE
    decision_timeout: Optional[float] = Field(default=None, gt=0)


def _find_pyproject(start: Path) -> Optional[Path]:
    for directory in (start, *start.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


@functools.cache
def _read_pyproject_settings(cwd: Path) -> tuple[Optional[Path], dict[str, Any]]:
    path = _find_pyproject(cwd)
    if path is None:
        return None, {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    section = data.get("tool", {}).get("maverick", {})
    if not isinstance(section, dict):
        raise ValueError(f"[tool.maverick] in {path} must be a table")
    return path, section


def _clear_config_cache() -> None:
    """Forget the cached ``pyproject.toml`` lookups (used by tests)."""
    _read_pyproject_settings.cache_clear()


def resolve_settings(
    player_isolation: Optional[PlayerIsolation | str] = None,
    decision_timeout: Optional[float] = None,
) -> IsolationSettings:
    """Resolve the isolation settings from code, environment and ``pyproject.toml``.

    Parameters
    ----------
    player_isolation : PlayerIsolation | str | None, optional
        Explicit isolation mode. Overrides every other source if provided.
    decision_timeout : float | None, optional
        Explicit decision timeout in seconds. Overrides every other source if provided.

    Returns
    -------
    IsolationSettings
        The validated settings.

    Raises
    ------
    ValueError
        If a value is invalid, or ``[tool.maverick]`` contains unknown keys. The
        message names the source of the invalid value.

    .. versionadded:: 0.7.0
    """
    pyproject_path, pyproject = _read_pyproject_settings(Path.cwd())
    unknown = set(pyproject) - set(IsolationSettings.model_fields)
    if unknown:
        raise ValueError(
            f"Unknown key(s) in [tool.maverick] of {pyproject_path}: "
            f"{', '.join(sorted(unknown))}"
        )

    explicit = {
        "player_isolation": player_isolation,
        "decision_timeout": decision_timeout,
    }
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}
    for field, env_var in ENV_VARS.items():
        env_value = os.environ.get(env_var, "").strip()
        if explicit[field] is not None:
            values[field], sources[field] = explicit[field], "argument"
        elif env_value:
            values[field] = env_value
            sources[field] = f"environment variable {env_var}"
        elif field in pyproject:
            values[field] = pyproject[field]
            sources[field] = f"[tool.maverick] in {pyproject_path}"

    try:
        return IsolationSettings.model_validate(values)
    except ValidationError as exc:
        details = "; ".join(
            f"{err['loc'][0]} from {sources.get(err['loc'][0], 'unknown source')}: "
            f"{err['msg']}"
            for err in exc.errors()
        )
        raise ValueError(f"Invalid maverick settings: {details}") from exc
