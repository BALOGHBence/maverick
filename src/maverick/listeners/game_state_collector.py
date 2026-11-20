from maverick.enums import GameEventType
from maverick.events import GameEvent
from maverick.game import Game

__all__ = ["GameStateCollector"]


class GameStateCollector:
    """Collects a snapshot of the game state after every event.

    Each entry in :attr:`states` is a plain dictionary produced by serializing
    the :class:`~maverick.state.GameState` at the moment an event fires,
    enriched with two extra keys:

    - ``ts`` — the timestamp of the triggering event.
    - ``event_uid`` — the UID of the triggering event.

    Parameters
    ----------
    game : Game, optional
        If provided, the collector subscribes to the game immediately.
    event_types : list[GameEventType], optional
        Restrict collection to these event types. If ``None`` or omitted,
        all event types are collected.

    Examples
    --------
    .. code-block:: python

        # Collect on every event
        collector = GameStateCollector(game)
        game.start()
        print(len(collector.states))  # one entry per event emitted

        # Collect only on hand boundaries
        from maverick import GameEventType
        collector = GameStateCollector(
            game,
            event_types=[GameEventType.HAND_STARTED, GameEventType.HAND_ENDED],
        )
    """

    def __init__(
        self,
        game: Game | None = None,
        event_types: list[GameEventType] | None = None,
    ):
        self.states: list[dict] = []
        self.listen(game, event_types)

    def listen(
        self,
        game: Game | None = None,
        event_types: list[GameEventType] | None = None,
    ) -> None:
        """Subscribe to events on *game*.

        Can be called after construction to attach the collector to a game
        that was not available at instantiation time.

        Parameters
        ----------
        game : Game, optional
            The game to listen to. Does nothing if ``None``.
        event_types : list[GameEventType], optional
            The event types to listen to. If ``None`` or omitted, all event
            types are subscribed.
        """
        if game is None:
            return
        types = event_types if event_types is not None else list(GameEventType)
        invalid = [t for t in types if not isinstance(t, GameEventType)]
        if invalid:
            raise TypeError(
                f"All event_types must be GameEventType members, got: {invalid}"
            )
        self.game = game
        for event_type in types:
            game.subscribe(event_type, self._handle_event)

    def _handle_event(self, event: GameEvent, game: Game) -> None:
        event_dict = event.model_dump(mode="json")
        state_dict = game.state.model_dump(mode="json")
        state_dict["ts"] = event_dict["ts"]
        state_dict["event_uid"] = event_dict["uid"]
        self.states.append(state_dict)
