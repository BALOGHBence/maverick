"""
Saved games on disk.

A saved game is a directory with three files:

- ``header.json``: written once when the game starts. Format version, Maverick version,
  rules, settings that affect the game, and the players at the table.
- ``events.jsonl``: an append-only log with one line per event, each with the full
  game state after it. Used for replay (:class:`~maverick.replay.Replay`).
- ``checkpoint.json``: the state of the engine at the end of the last completed hand,
  including the state of its random number generator and the state each player
  exports. Used to resume the game (:meth:`Game.load <maverick.game.Game.load>`).

Everything is JSON, validated with Pydantic models when it is read. A saved game never
contains pickled data and never names code to import, because save files are shared
and loaded later, and loading either would run code.

The engine writes the events of a hand to the log only once the hand is over, together
with the checkpoint, so the files on disk never hold the hole cards of a hand that is
still being played. The checkpoint is written to a temporary file that then replaces
the old one, so a crash can't corrupt the last good checkpoint. If a game is
interrupted, the log may hold events that came after the checkpoint. They are cut off
when the game is loaded.

.. versionadded:: 0.7.0
"""

from __future__ import annotations

import json
import os
import time
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .events import GameEvent
from .rules import PokerRules
from .state import GameState

__all__ = [
    "SAVE_FORMAT_VERSION",
    "SaveFormatError",
    "SaveHeader",
    "SeatRecord",
    "Checkpoint",
    "TableRecord",
    "PlayerRecord",
    "EventRecord",
]

#: Version of the save format written by this version of Maverick.
SAVE_FORMAT_VERSION = 1
#: Versions of the save format this version of Maverick can read.
SUPPORTED_FORMAT_VERSIONS = frozenset({1})

HEADER_FILE = "header.json"
EVENTS_FILE = "events.jsonl"
CHECKPOINT_FILE = "checkpoint.json"

# Save files are secret while a game runs: the checkpoint predicts the next cards.
# Keep other operating system users out.
_DIR_MODE = 0o700
_FILE_MODE = 0o600


class SaveFormatError(ValueError):
    """A saved game is missing, malformed, or uses an unsupported format version.

    .. versionadded:: 0.7.0
    """


class _Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SeatRecord(_Record):
    """A player at the table when the game started.

    .. versionadded:: 0.7.0
    """

    uid: str
    name: str
    seat: int = Field(ge=0)


class SaveHeader(_Record):
    """Contents of ``header.json``: what doesn't change while a game runs.

    .. versionadded:: 0.7.0
    """

    format_version: int
    maverick_version: str
    created_at: float
    game_uid: str
    rules: PokerRules
    seed: int
    max_hands: int
    first_button_position: Optional[int] = None
    players: list[SeatRecord]


class TableRecord(_Record):
    """The seats of the table and the position of the button.

    .. versionadded:: 0.7.0
    """

    seats: list[Optional[str]]
    button_seat: Optional[int] = None


class PlayerRecord(_Record):
    """What a player exported at a checkpoint.

    Fields
    ------
    state : dict | None
        What the player's ``export_state`` returned.
    export_failed : bool
        Whether ``export_state`` failed. The player is then restored without state when
        the game is loaded.

    .. versionadded:: 0.7.0
    """

    state: Optional[dict[str, Any]] = None
    export_failed: bool = False


class Checkpoint(_Record):
    """Contents of ``checkpoint.json``: the engine between two hands.

    .. versionadded:: 0.7.0
    """

    format_version: int
    game_uid: str
    created_at: float
    events: int = Field(ge=0, description="Number of event log lines it covers")
    log_size: int = Field(ge=0, description="Size of the event log in bytes")
    state: GameState
    table: TableRecord
    all_stacks_at_game_start: int
    revealed_uids: list[str]
    rng_state: tuple[int, list[int], Optional[float]]
    players: dict[str, PlayerRecord]


class EventRecord(_Record):
    """One line of ``events.jsonl``: an event and the game state right after it.

    .. versionadded:: 0.7.0
    """

    event: GameEvent
    state: GameState


def maverick_version() -> str:
    """The installed version of Maverick."""
    return package_version("maverick")


# ---------------------------------------------------------------------------- reading


def _check_version(data: Any, what: str) -> None:
    if not isinstance(data, dict):
        raise SaveFormatError(f"The {what} is not a JSON object")
    found = data.get("format_version")
    if found not in SUPPORTED_FORMAT_VERSIONS:
        supported = ", ".join(str(v) for v in sorted(SUPPORTED_FORMAT_VERSIONS))
        raise SaveFormatError(
            f"The {what} uses save format version {found!r}, but Maverick "
            f"{maverick_version()} only reads version {supported}. Load it with the "
            f"Maverick version that saved it."
        )


def _read_json_file(path: Path, what: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SaveFormatError(f"The {what} {path} doesn't exist") from exc
    try:
        return json.loads(text)
    except ValueError as exc:
        raise SaveFormatError(f"The {what} {path} is not valid JSON: {exc}") from exc


def read_header(directory: Path) -> SaveHeader:
    """Read and validate ``header.json`` of a saved game."""
    data = _read_json_file(directory / HEADER_FILE, "header of the saved game")
    _check_version(data, "saved game")
    try:
        return SaveHeader.model_validate(data)
    except ValidationError as exc:
        raise SaveFormatError(
            f"The header of the saved game is invalid: {exc}"
        ) from exc


def read_checkpoint(directory: Path) -> Checkpoint:
    """Read and validate ``checkpoint.json`` of a saved game."""
    data = _read_json_file(directory / CHECKPOINT_FILE, "checkpoint")
    _check_version(data, "checkpoint")
    try:
        return Checkpoint.model_validate(data)
    except ValidationError as exc:
        raise SaveFormatError(f"The checkpoint is invalid: {exc}") from exc


def read_event_lines(directory: Path, limit: Optional[int] = None) -> list[dict]:
    """Read the lines of the event log as JSON objects, without validating them.

    A last line without a line break was cut off by a crash and is ignored.

    Parameters
    ----------
    directory : Path
        The directory of the saved game.
    limit : int | None
        Read at most this many lines.
    """
    path = directory / EVENTS_FILE
    lines: list[dict] = []
    try:
        handle = path.open("r", encoding="utf-8", newline="\n")
    except FileNotFoundError as exc:
        raise SaveFormatError(f"The event log {path} doesn't exist") from exc
    with handle:
        for number, line in enumerate(handle, start=1):
            if limit is not None and len(lines) >= limit:
                break
            if not line.endswith("\n"):
                break
            try:
                data = json.loads(line)
            except ValueError as exc:
                raise SaveFormatError(
                    f"Line {number} of the event log is not valid JSON: {exc}"
                ) from exc
            if not isinstance(data, dict):
                raise SaveFormatError(f"Line {number} of the event log is malformed")
            lines.append(data)
    return lines


def parse_event(data: dict, number: int) -> GameEvent:
    """Validate the event of one line of the event log (``number`` starts at 1)."""
    try:
        return GameEvent.model_validate(data.get("event"))
    except ValidationError as exc:
        raise SaveFormatError(
            f"Line {number} of the event log holds an invalid event: {exc}"
        ) from exc


def parse_state(data: dict, number: int) -> GameState:
    """Validate the state of one line of the event log (``number`` starts at 1)."""
    try:
        return GameState.model_validate(data.get("state"))
    except ValidationError as exc:
        raise SaveFormatError(
            f"Line {number} of the event log holds an invalid state: {exc}"
        ) from exc


# ---------------------------------------------------------------------------- writing


def _fsync_directory(directory: Path) -> None:
    """Make a rename in ``directory`` durable. Not possible on every platform."""
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:  # pragma: no cover - e.g. Windows
        return
    try:
        os.fsync(fd)
    except OSError:  # pragma: no cover
        pass
    finally:
        os.close(fd)


def _write_atomically(path: Path, text: str) -> None:
    """Write ``text`` to a temporary file and rename it to ``path``."""
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _FILE_MODE)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    _fsync_directory(path.parent)


def directory_has_save(directory: Path) -> bool:
    """Whether ``directory`` already holds a saved game."""
    return (directory / HEADER_FILE).exists()


class SaveWriter:
    """Writes a saved game while the game runs.

    Events are kept in memory until :meth:`commit` or :meth:`flush` writes them, so a
    hand's events reach the disk only once the hand is over.

    Parameters
    ----------
    directory : Path
        The directory of the saved game.
    events : int
        Number of lines already in the event log, when continuing a loaded game.
    """

    def __init__(self, directory: Path, *, events: int = 0) -> None:
        self.directory = directory
        self._pending: list[str] = []
        self._written = events

    def create(self, header: SaveHeader) -> None:
        """Create the directory, the header and an empty event log."""
        if directory_has_save(self.directory):
            raise FileExistsError(
                f"{self.directory} already holds a saved game. Use Game.load to "
                f"continue it, or choose another directory."
            )
        self.directory.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
        fd = os.open(
            self.directory / EVENTS_FILE,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            _FILE_MODE,
        )
        os.close(fd)
        _write_atomically(
            self.directory / HEADER_FILE, header.model_dump_json(indent=2)
        )

    def record(self, event: GameEvent, state: GameState) -> None:
        """Remember an event and the state after it, to be written later."""
        line = json.dumps(
            {
                "event": event.model_dump(mode="json"),
                "state": state.model_dump(mode="json"),
            },
            separators=(",", ":"),
        )
        self._pending.append(line + "\n")

    def flush(self) -> int:
        """Append the remembered events to the log and return the log's size."""
        path = self.directory / EVENTS_FILE
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, _FILE_MODE)
        with os.fdopen(fd, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(self._pending))
            handle.flush()
            os.fsync(handle.fileno())
            size = handle.tell()
        self._written += len(self._pending)
        self._pending.clear()
        return size

    def commit(self, build_checkpoint: Callable[[int, int], Checkpoint]) -> None:
        """Write the remembered events, then a new checkpoint.

        Parameters
        ----------
        build_checkpoint : Callable[[int, int], Checkpoint]
            Called with the number of lines and the size of the event log, returns the
            checkpoint to write.
        """
        size = self.flush()
        checkpoint = build_checkpoint(self._written, size)
        _write_atomically(
            self.directory / CHECKPOINT_FILE, checkpoint.model_dump_json()
        )


def truncate_event_log(directory: Path, size: int) -> None:
    """Cut the event log off after ``size`` bytes, dropping events of unfinished hands."""
    path = directory / EVENTS_FILE
    if path.stat().st_size < size:
        raise SaveFormatError(
            f"The event log {path} is shorter than the checkpoint expects"
        )
    os.truncate(path, size)


def new_header(**fields: Any) -> SaveHeader:
    """Build a header for a new saved game."""
    return SaveHeader(
        format_version=SAVE_FORMAT_VERSION,
        maverick_version=maverick_version(),
        created_at=time.time(),
        **fields,
    )
