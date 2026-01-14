from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional
import uuid
import logging

from pydantic import BaseModel, ConfigDict

from .protocol import EventHandler
from .enums import GameEventType

if TYPE_CHECKING:  # pragma: no cover
    from .game import Game
    from .events import GameEvent

__all__ = ["EventBus", "Subscription"]

log = logging.getLogger("maverick.events")


class Subscription(BaseModel):
    """Immutable subscription record."""

    token: str
    event_type: GameEventType
    handler: EventHandler
    priority: int = 0
    once: bool = False
    filter: Optional[Callable[[Any], bool]] = None

    model_config = ConfigDict(
        frozen=True,  # Makes the model immutable
        extra="forbid",  # Prevents accidental fields
        arbitrary_types_allowed=True,
    )


class EventBus:
    """Simple event bus for managing event subscriptions and emissions.

    Parameters
    ----------
    strict : bool
        If True, exceptions in event handlers will propagate. Otherwise, they will be logged.
    """

    def __init__(self, *, strict: bool = False):
        self._subs: list[Subscription] = []
        self._strict = strict

    def subscribe(
        self,
        event_type: GameEventType,
        handler: EventHandler,
        *,
        priority: int = 0,
        once: bool = False,
        filter: Optional[Callable[[Any], bool]] = None,
    ) -> str:
        """Subscribe to an event type with a handler.

        Parameters
        ----------
        event_type : str
            The type of event to subscribe to.
        handler : EventHandler
            The function to call when the event is emitted.
        priority : int
            Priority of the handler; higher priority handlers are called first.
        once : bool
            If True, the handler will be removed after the first call.
        filter : Optional[Callable[[Any], bool]]
            Optional filter function to determine if the handler should be called.
        """
        token = uuid.uuid4().hex
        self._subs.append(
            Subscription(
                token=token,
                event_type=event_type,
                handler=handler,
                priority=priority,
                once=once,
                filter=filter,
            )
        )
        # higher priority first
        self._subs.sort(key=lambda s: s.priority, reverse=True)
        return token

    def unsubscribe(self, token: str) -> None:
        """Unsubscribe a handler using its token."""
        self._subs = [s for s in self._subs if s.token != token]

    def emit(self, event: "GameEvent", game: "Game") -> None:
        """Emit an event to all subscribed handlers."""
        # iterate over a snapshot so handlers can subscribe/unsubscribe safely
        subs = list(self._subs)
        to_remove: list[str] = []

        for s in subs:
            if getattr(event, "type", None) != s.event_type:
                continue
            if s.filter is not None and not s.filter(event):
                continue

            try:
                s.handler(event, game)
            except Exception:
                if self._strict:
                    raise
                log.exception("Event handler failed: %s", s, exc_info=True)

            if s.once:
                to_remove.append(s.token)

        for token in to_remove:
            self.unsubscribe(token)
