"""Running players in worker processes, isolated from the game engine."""

from .proxy import PlayerFailure, ProcessPlayer

__all__ = ["PlayerFailure", "ProcessPlayer"]
