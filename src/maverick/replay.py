"""
Replay of saved games.

:class:`Replay` reads a game saved with ``Game(save_dir=...)`` and steps through it,
event by event or hand by hand, without creating a :class:`~maverick.game.Game` or any
players.

.. versionadded:: 0.7.0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

from .enums import GameEventType
from .events import GameEvent
from .rules import PokerRules
from .savegame import (
    SaveHeader,
    SeatRecord,
    parse_event,
    parse_state,
    read_event_lines,
    read_header,
)
from .state import GameState

__all__ = ["Replay"]


class Replay:
    """Steps through a saved game without the players.

    Every step is one event of the game, together with the full game state right after
    it, including the hole cards of every player. A cursor marks the current step;
    :meth:`forward`, :meth:`backward`, :meth:`seek` and :meth:`go_to_hand` move it.

    The replay holds every event that was written to the save, including those of a
    hand that was interrupted and not resumed yet, as long as they reached the disk.
    ``GAME_STATE_CHANGED`` events are not saved.

    Parameters
    ----------
    save_dir : str | os.PathLike
        The directory the game was saved to.

    Raises
    ------
    SaveFormatError
        If the save is missing, malformed, or was written in an unsupported format
        version.

    Examples
    --------
    .. code-block:: python

        from maverick import Replay

        replay = Replay("saves/game-1")
        replay.go_to_hand(3)
        while replay.forward():
            print(replay.event.type.name, replay.state.pot)
            if replay.event.type.name == "HAND_ENDED":
                break

    .. versionadded:: 0.7.0
    """

    def __init__(self, save_dir: str | os.PathLike) -> None:
        directory = Path(save_dir)
        self._header = read_header(directory)
        self._lines = read_event_lines(directory)
        self._events = tuple(
            parse_event(line, n) for n, line in enumerate(self._lines, start=1)
        )
        # States are validated when they are first needed, because there are many.
        self._states: list[Optional[GameState]] = [None] * len(self._events)
        self._position = 0

    @property
    def header(self) -> SaveHeader:
        """The header of the save."""
        return self._header

    @property
    def rules(self) -> PokerRules:
        """The rules of the game."""
        return self._header.rules

    @property
    def game_uid(self) -> str:
        """The UID of the game."""
        return self._header.game_uid

    @property
    def seed(self) -> int:
        """The seed of the game's random number generator."""
        return self._header.seed

    @property
    def players(self) -> list[SeatRecord]:
        """The players at the table when the game started."""
        return list(self._header.players)

    @property
    def events(self) -> tuple[GameEvent, ...]:
        """All events, in order."""
        return self._events

    @property
    def hand_numbers(self) -> list[int]:
        """The numbers of the hands that were started, in order."""
        return [
            e.hand_number for e in self._events if e.type == GameEventType.HAND_STARTED
        ]

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[tuple[GameEvent, GameState]]:
        """Iterate over all steps as ``(event, state)`` pairs. Doesn't move the cursor."""
        for index in range(len(self._events)):
            yield self._events[index], self.state_at(index)

    def state_at(self, index: int) -> GameState:
        """The game state right after the event at ``index``."""
        if not 0 <= index < len(self._events):
            raise IndexError(f"Step {index} is out of range")
        state = self._states[index]
        if state is None:
            state = self._states[index] = parse_state(self._lines[index], index + 1)
        return state

    @property
    def position(self) -> int:
        """The index of the current step."""
        return self._position

    @property
    def event(self) -> GameEvent:
        """The event of the current step."""
        if not self._events:
            raise IndexError("The replay has no events")
        return self._events[self._position]

    @property
    def state(self) -> GameState:
        """The game state right after the event of the current step."""
        return self.state_at(self._position)

    def seek(self, index: int) -> GameEvent:
        """Move to the step at ``index`` and return its event.

        Negative indexes count from the end, as for lists.
        """
        if index < 0:
            index += len(self._events)
        if not 0 <= index < len(self._events):
            raise IndexError(f"Step {index} is out of range")
        self._position = index
        return self._events[index]

    def forward(self, steps: int = 1) -> bool:
        """Move up to ``steps`` steps forward.

        Returns
        -------
        bool
            False if the cursor was already at the last step, True otherwise.
        """
        target = min(self._position + steps, len(self._events) - 1)
        moved = target > self._position
        self._position = max(target, 0)
        return moved

    def backward(self, steps: int = 1) -> bool:
        """Move up to ``steps`` steps backward.

        Returns
        -------
        bool
            False if the cursor was already at the first step, True otherwise.
        """
        target = max(self._position - steps, 0)
        moved = target < self._position
        self._position = target
        return moved

    def go_to_hand(self, hand_number: int) -> GameEvent:
        """Move to the ``HAND_STARTED`` event of a hand and return it.

        Raises
        ------
        KeyError
            If the hand was not played.
        """
        for index, event in enumerate(self._events):
            if (
                event.type == GameEventType.HAND_STARTED
                and event.hand_number == hand_number
            ):
                self._position = index
                return event
        raise KeyError(f"Hand {hand_number} was not played")

    def hand(self, hand_number: int) -> list[tuple[GameEvent, GameState]]:
        """All steps of a hand, from ``HAND_STARTED`` up to and including ``HAND_ENDED``.

        Doesn't move the cursor.

        Raises
        ------
        KeyError
            If the hand was not played.
        """
        steps = []
        started = False
        for index, event in enumerate(self._events):
            if not started:
                started = (
                    event.type == GameEventType.HAND_STARTED
                    and event.hand_number == hand_number
                )
            if started:
                steps.append((event, self.state_at(index)))
                if event.type == GameEventType.HAND_ENDED:
                    break
        if not steps:
            raise KeyError(f"Hand {hand_number} was not played")
        return steps
