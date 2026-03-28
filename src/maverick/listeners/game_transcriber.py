from maverick import (
    Game,
    GameEvent,
    GameEventType,
    PlayerAction,
    ActionType,
)

__all__ = ["GameTranscriber"]


class GameTranscriber:
    """Produces a human-readable transcript of a poker game.

    Subscribes to all game events and converts them into formatted text lines
    stored in an internal log. The full transcript is exposed via the
    :attr:`history` property as a single newline-joined string.

    Raw event payloads are also preserved in :attr:`event_dump` for
    programmatic inspection.

    Parameters
    ----------
    game : Game, optional
        If provided, the transcriber subscribes to the game immediately.

    Examples
    --------
    .. code-block:: python

        transcriber = GameTranscriber(game)
        game.start()
        print(transcriber.history)
    """

    def __init__(self, game: Game | None = None):
        self.game = game
        self.events = []
        self.uid_to_player = {}
        self.max_line_length = 80
        self.event_dump = []

        self.listen(game)

    def listen(self, game: Game = None) -> None:
        """Subscribe to all events on *game*.

        Can be called after construction to attach the transcriber to a game
        that was not available at instantiation time.

        Parameters
        ----------
        game : Game, optional
            The game to listen to. Does nothing if ``None``.
        """
        if game is None:
            return

        self.game = game
        self._subscribe_to_events()
        self._register_players()

    def _subscribe_to_events(self) -> None:
        for event_type in GameEventType:
            self.game.subscribe(event_type, self._handle_event)

    def _register_players(self) -> None:
        self.uid_to_player = {player.uid: player for player in self.game.state.players}

    @property
    def history(self) -> str:
        """The full game transcript as a single newline-joined string."""
        return "\n".join(self.events)

    def _log_betting_round_started(self) -> None:
        if len(self.game.state.community_cards) == 0:
            self.events.append("Community cards: None")
        else:
            self.events.append(
                f"Community cards: {[card.code() for card in self.game.state.community_cards]}"
            )

        current_bet = self.game.state.current_bet
        current_pot = self.game.state.pot
        last_raise_size = self.game.state.last_raise_size
        self.events.append(
            (
                f"Current pot size: {current_pot}. "
                f"Current bet: {current_bet}. "
                f"Minimum raise size: {last_raise_size}."
            )
        )

        self.events.append("")

    def _log_section_header(
        self, title: str, chr: str, *, add_empty_line: bool = True
    ) -> None:
        len_title = len(title) + 2 if len(title) > 0 else 0
        len_prefix_suffix = (self.max_line_length - len_title) // 2
        title = f" {title} " if len_title > 0 else ""
        msg = chr * len_prefix_suffix + f"{title}" + chr * len_prefix_suffix
        if len(msg) < self.max_line_length:
            msg += chr
        elif len(msg) > self.max_line_length:
            msg = msg[: self.max_line_length]
        msg = msg[: self.max_line_length]
        self.events.append(msg)
        if add_empty_line:
            self.events.append("")

    def _handle_event(self, event: GameEvent, game: Game) -> None:
        """Dispatch an incoming event to the appropriate log method."""
        event_dict = event.model_dump(mode="json")
        self.event_dump.append(event_dict)

        hand_number = game.state.hand_number

        match event.type:
            case GameEventType.GAME_STARTED:
                self._log_section_header("", "=", add_empty_line=False)
                self._log_section_header(f"Game Started", "=", add_empty_line=False)
                self._log_section_header("", "=")

                self.events.append("Game type: No-Limit Texas Hold'em")
                self.events.append(f"Small blind: {game.state.small_blind}")
                self.events.append(f"Big blind: {game.state.big_blind}")
                self.events.append(f"Ante: {game.state.ante}")
                self.events.append("")

                self.events.append("Players at the table:")
                for player in self.game.state.players:
                    self.events.append(
                        f"    {player.name}: Starting stack {player.state.stack}"
                    )
                self.events.append("")

            case GameEventType.HAND_STARTED:
                if len(self.events) > 0 and len(self.events[-1].strip()) > 0:
                    self.events.append("")

                self._log_section_header(f"Hand {hand_number}", "=")

                button_player = game.button
                self.events.append(f"{button_player.name} is on the button.")

                small_blind_player = game.small_blind
                self.events.append(f"{small_blind_player.name} is the small blind.")

                big_blind_player = game.big_blind
                self.events.append(f"{big_blind_player.name} is the big blind.")

                big_blind_seat = game.table.get_player_seat(big_blind_player)
                players_in_hand = game.state.get_players_in_hand()
                active_uids = {player.uid for player in players_in_hand}
                utg_position = game.table.next_occupied_seat(
                    big_blind_seat, active_uids=active_uids
                )
                utg_player_uid = game.table[utg_position]
                utg_player = self.uid_to_player[utg_player_uid]
                self.events.append(f"{utg_player.name} is under the gun.")

                self.events.append("")

                self.events.append(
                    f"Player stacks at the beginning of hand {hand_number}:"
                )
                for player in game.state.players:
                    self.events.append(f"    {player.name}: {player.state.stack}")
                self.events.append("")

            case GameEventType.BETTING_ROUND_STARTED:
                street_name = game.state.street.name
                self._log_section_header(
                    f"Hand: {hand_number} | Street: {street_name}", "-"
                )
                self._log_betting_round_started()

            case GameEventType.PLAYER_ACTION_TAKEN:
                action: PlayerAction = event.action
                player_uid = event.player_uid
                player = self.uid_to_player[player_uid]
                current_bet = game.state.current_bet
                current_pot = game.state.pot
                last_raise_size = game.state.last_raise_size

                match action.action_type:
                    case ActionType.FOLD:
                        self.events.append(
                            f"[{player.name}] folds. Remaining stack: {player.state.stack}."
                        )
                    case ActionType.CALL:
                        self.events.append(
                            f"[{player.name}] calls. Remaining stack: {player.state.stack}."
                        )
                    case ActionType.RAISE:
                        self.events.append(
                            f"[{player.name}] raises bet to {current_bet}. Remaining stack: {player.state.stack}."
                        )
                    case ActionType.CHECK:
                        self.events.append(
                            f"[{player.name}] checks. Remaining stack: {player.state.stack}."
                        )
                    case ActionType.BET:
                        self.events.append(
                            f"[{player.name}] bets {action.amount}. Remaining stack: {player.state.stack}."
                        )

                self.events.append(
                    (
                        f"Current pot size: {current_pot}. "
                        f"Current bet: {current_bet}. "
                        f"Minimum raise size: {last_raise_size}."
                    )
                )

            case GameEventType.BETTING_ROUND_COMPLETED:
                self.events.append("")
                self.events.append(f"Player standings after the betting round:")
                for player in game.state.players:
                    player_pot = player.state.total_contributed
                    state_type = player.state.state_type.name
                    self.events.append(
                        f"    {player.name}: State={state_type}, Pot={player_pot}, Stack={player.state.stack}"
                    )
                self.events.append("")

            case GameEventType.SHOWDOWN_STARTED:
                self._log_section_header(f"Hand: {hand_number} | SHOWDOWN", "-")

            case GameEventType.PLAYER_CARDS_REVEALED:
                player_uid = event.player_uid
                player = self.uid_to_player[player_uid]
                payload = event.payload
                self.events.append(
                    (
                        f"{player.name} reveals: {payload['holding']}. "
                        f"Best hand: {payload['best_hand']} ({payload['best_hand_type']}). "
                        f"Hand score: {payload['best_score']}."
                    )
                )

            case GameEventType.SHOWDOWN_COMPLETED:
                self.events.append("")
                self.events.append(f"Player stacks after showdown:")
                for player in game.state.players:
                    self.events.append(f"    {player.name}: {player.state.stack}")
                self.events.append("")

            case GameEventType.POT_WON:
                player_uid = event.player_uid
                player = self.uid_to_player[player_uid]
                amount = event.payload.get("amount", 0)
                self.events.append(f"{player.name} wins {amount}.")

            case GameEventType.PLAYER_ELIMINATED:
                player_uid = event.player_uid
                player = self.uid_to_player[player_uid]
                self.events.append(f"{player.name} has been eliminated from the game.")

            case GameEventType.HAND_ENDED:
                pass
