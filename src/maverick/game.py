"""
Poker Game State Machine.

This module implements a complete poker game using a state machine
architecture. The game manages player actions, betting rounds, card dealing, and
pot distribution.
"""

from __future__ import annotations

from typing import Deque, Optional
from collections import deque
import logging
from warnings import warn

from .deck import Deck
from .enums import (
    ActionType,
    GameEventType,
    GameStateType,
    PlayerStateType,
    Street,
    Suit,
)
from .events import GameEvent
from .holding import Holding
from .protocol import PlayerLike, EventHandler
from .state import GameState
from .playeraction import PlayerAction
from .playerstate import PlayerState
from .utils import find_highest_scoring_hand
from .eventbus import EventBus
from .rules import PokerRules, DealingRules, StakesRules, ShowdownRules

__all__ = ["Game"]


class Game:
    """
    Texas Hold'em Poker Game.

    Implements a Texas Hold'em poker game using an event-driven state machine.
    The game manages player actions, betting rounds, dealing, and pot distribution.

    Parameters
    ----------
    small_blind : int
        Amount for the small blind.
    big_blind : int
        Amount for the big blind.
    ante : int
        Amount for the ante.
    min_players : int
        Minimum number of players to start the game.
    max_players : int
        Maximum number of players allowed at the table.
    max_hands : int
        Maximum number of hands to play before ending the game. Default is 1000.
    exc_handling_mode : {"log", "raise"}
        If "raise", exceptions in event handlers will propagate. If "log", they will be logged. This setting
        only effects event handling, not game logic. If an exception occurs in game logic, it will always raise.
    log_events : bool
        If True, game events will be logged to the console. This only affects logging, not event handling.
        The purpose of this is allow users to have their own event handlers without excessive logging noise.
    rules : PokerRules | None
        Custom poker rules to use. If None, default Texas Hold'em rules are applied. When provided, other
        parameters (small_blind, big_blind, ante, min_players, max_players) will override the corresponding
        fields in the rules.
    first_button_position : int | None
        The seat index of the player who will be the button in the first hand. If None (the default), the
        button is assigned randomly using a card draw.
    """

    def __init__(
        self,
        *,
        small_blind: Optional[int] = None,
        big_blind: Optional[int] = None,
        ante: Optional[int] = None,
        min_players: Optional[int] = 2,
        max_players: Optional[int] = None,
        max_hands: int = 1000,
        exc_handling_mode: str = "log",
        log_events: bool = True,
        rules: Optional[PokerRules] = None,
        first_button_position: Optional[int] = None,
    ):
        if not exc_handling_mode in ["log", "raise"]:
            raise ValueError("exc_handling_mode must be 'log' or 'raise'")

        if rules is None:
            rules = PokerRules(
                dealing=DealingRules(),
                stakes=StakesRules(
                    small_blind=small_blind,
                    big_blind=big_blind,
                ),
                showdown=ShowdownRules(),
            )

        if small_blind:
            rules.stakes.small_blind = small_blind

        if big_blind:
            rules.stakes.big_blind = big_blind

        if ante:
            rules.stakes.ante = ante

        if min_players:
            rules.dealing.min_players = min_players

        if max_players:
            rules.dealing.max_players = max_players

        if first_button_position is not None:
            if not isinstance(first_button_position, int):
                raise ValueError("first_button_position must be an integer")

            if not first_button_position >= 0:
                raise ValueError("first_button_position must be non-negative")

        self._rules = rules
        self.max_hands = max_hands
        self._state = GameState(
            small_blind=rules.stakes.small_blind,
            big_blind=rules.stakes.big_blind,
            ante=rules.stakes.ante,
        )
        self._event_queue: Deque[GameEventType] = deque()
        self._logger = logging.getLogger("maverick")
        self._log_events = log_events
        self._first_button_position = first_button_position

        # Event handling
        self._events = EventBus(strict=exc_handling_mode == "raise")
        self._event_history: list[GameEvent] = []

    @property
    def rules(self) -> PokerRules:
        """Returns the poker rules used in this game."""
        return self._rules

    @property
    def state(self) -> GameState:
        """Returns the current game state."""
        return self._state

    @property
    def history(self) -> list[GameEvent]:
        """Returns the event history.

        Returns
        -------
        list[GameEvent]
            A list of all game events in chronological order.
        """
        return self._event_history

    def _log(
        self,
        message: str,
        loglevel: int = logging.INFO,
        street_prefix: bool = True,
        **kwargs,
    ) -> None:
        if not self._log_events:
            return

        # ANSI colors (set NO_COLOR=1 to disable)
        color_map = {
            Street.PRE_FLOP: "\033[38;5;39m",  # blue
            Street.FLOP: "\033[38;5;34m",  # green
            Street.TURN: "\033[38;5;214m",  # orange
            Street.RIVER: "\033[38;5;196m",  # red
            Street.SHOWDOWN: "\033[38;5;201m",  # magenta
        }
        reset = "\033[0m"

        street = self.state.street
        street_name = street.name
        street_prefix_msg = f"{color_map.get(street, '')}{street_name}{reset}"

        msg = f"{street_prefix_msg} | {message}" if street_prefix else message
        self._logger.log(loglevel, msg, **kwargs)

    def subscribe(
        self, event_type: GameEventType, handler: EventHandler, **kwargs
    ) -> str:
        """
        Register a handler for a specific game event type.

        Handlers are called synchronously in registration order when the event occurs.
        Exceptions in handlers are caught, logged, and do not interrupt engine execution.

        Parameters
        ----------
        event_type : GameEventType
            The type of event to listen for.
        handler : EventHandler
            A callable that accepts a GameEvent and returns None.
        """
        return self._events.subscribe(event_type, handler, **kwargs)

    def unsubscribe(self, token: str) -> None:
        """Unsubscribe a handler using its token.

        Parameters
        ----------
        token : str
            The subscription token returned by the subscribe method.
        """
        return self._events.unsubscribe(token)

    def _emit(self, event: GameEvent) -> None:
        """
        Emit a game event to all registered handlers.

        Dispatches the event to handlers in registration order. Exceptions in handlers
        are caught and logged to prevent disruption of engine execution.

        Parameters
        ----------
        event : GameEvent
            The event to emit to handlers.
        """
        self._event_history.append(event)

        # external listeners
        self._events.emit(event, self)

        # player hooks
        for p in self.state.players:
            fn = getattr(p, "on_event", None)
            if callable(fn):
                try:
                    fn(event, self)
                except Exception:
                    self._logger.warning(
                        f"Exception in player {p.name} on_event hook for {event.type.name}",
                        exc_info=True,
                    )
            specific = getattr(p, f"on_{event.type.name.lower()}", None)
            if callable(specific):
                try:
                    specific(event, self)
                except Exception:
                    self._logger.warning(
                        f"Exception in player {p.name} {specific.__name__} hook for {event.type.name}",
                        exc_info=True,
                    )

    def _create_event(
        self,
        event_type: GameEventType,
        player_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        payload: Optional[dict] = None,
    ) -> GameEvent:
        """
        Create a GameEvent with current game state.

        Parameters
        ----------
        event_type : GameEventType
            The type of event.
        player_id : Optional[str]
            ID of the player involved in the event.
        action : Optional[ActionType]
            Type of action taken (for PLAYER_ACTION events).

        Returns
        -------
        GameEvent
            An immutable event payload.
        """
        return GameEvent(
            type=event_type,
            hand_number=self.state.hand_number,
            street=self.state.street,
            player_id=player_id,
            action=action,
            payload=payload or {},
        )

    def add_player(self, player: PlayerLike) -> None:
        """Add a player to the game.

        Parameters
        ----------
        player : PlayerLike
            The player to add to the game.
        """
        if len(self.state.players) >= self.rules.dealing.max_players:
            raise ValueError("Table is full")

        if self.state.state_type not in [
            GameStateType.WAITING_FOR_PLAYERS,
            GameStateType.READY,
        ]:
            raise ValueError("Cannot add players while game is in progress")

        if player.state is None:
            player.state = PlayerState(
                seat=len(self.state.players),
                state_type=PlayerStateType.ACTIVE,
            )
        else:
            if player.state.seat is None:
                player.state.seat = len(self.state.players)
            if player.state.state_type is None:
                player.state.state_type = PlayerStateType.ACTIVE

        self.state.players.append(player)

        self._handle_event(GameEventType.PLAYER_JOINED)
        self._emit(self._create_event(GameEventType.PLAYER_JOINED, player_id=player.id))
        self._log(
            f"Player {player.name} joined the game.", logging.INFO, street_prefix=False
        )

    def remove_player(self, player: PlayerLike) -> None:
        """Remove a player from the game.

        Parameters
        ----------
        player : PlayerLike
            The player to remove from the game.
        """
        player_id = player.id

        if self.state.state_type not in [
            GameStateType.WAITING_FOR_PLAYERS,
            GameStateType.READY,
            GameStateType.HAND_COMPLETE,
            GameStateType.GAME_OVER,
        ]:
            raise ValueError("Cannot remove players while hand is in progress")

        player = next((p for p in self.state.players if p.id == player_id), None)
        if not player:
            raise ValueError(f"Player with id {player_id} not found")

        self.state.players = [p for p in self.state.players if p.id != player_id]

        self._handle_event(GameEventType.PLAYER_LEFT)
        self._emit(self._create_event(GameEventType.PLAYER_LEFT, player_id=player_id))
        self._log(
            f"Player {player.name} left the game.", logging.INFO, street_prefix=False
        )

    def start(self) -> None:
        """Start the poker game."""
        self._log("Game started.\n", logging.INFO, street_prefix=False)
        self._initialize_game()
        self._event_queue.append(GameEventType.GAME_STARTED)
        self._drain_event_queue()

    def _find_first_button_position(self) -> int:
        """Determine the button position for the first hand."""
        if isinstance(self._first_button_position, int):
            n_players = len(self.state.players)
            return self._first_button_position % n_players if n_players > 0 else 0

        n_players = len(self.state.players)
        if n_players == 0:
            return 0

        deck = Deck.standard_deck(shuffle=True)
        suit_priority = {
            Suit.SPADES: 3,
            Suit.HEARTS: 2,
            Suit.DIAMONDS: 1,
            Suit.CLUBS: 0,
        }

        best_index = 0
        best_score: tuple[int, int] | None = None

        for idx in range(len(self.state.players)):
            card = deck.deal(1)[0]
            score = (card.rank.value, suit_priority[card.suit])

            if best_score is None or score > best_score:
                best_score = score
                best_index = idx

        return best_index

    def _handle_event(self, event: GameEventType) -> None:
        match event:
            case GameEventType.GAME_STARTED:
                assert self.state.state_type == GameStateType.READY
                self.state.state_type = GameStateType.STARTED
                self._emit(self._create_event(GameEventType.GAME_STARTED))
                self._start_new_hand()
                self._event_queue.append(GameEventType.HAND_STARTED)

            case GameEventType.HAND_STARTED:
                assert self.state.state_type in [
                    GameStateType.STARTED,
                    GameStateType.HAND_COMPLETE,
                ]
                self.state.state_type = GameStateType.DEALING
                self._emit(self._create_event(GameEventType.HAND_STARTED))
                self._deal_hole_cards()
                self._emit(self._create_event(GameEventType.HOLE_CARDS_DEALT))
                self._event_queue.append(GameEventType.HOLE_CARDS_DEALT)

            case GameEventType.HOLE_CARDS_DEALT:
                assert self.state.state_type == GameStateType.DEALING
                self._post_blinds()
                self._emit(self._create_event(GameEventType.BLINDS_POSTED))
                self._event_queue.append(GameEventType.BLINDS_POSTED)

            case GameEventType.BLINDS_POSTED:
                assert self.state.state_type == GameStateType.DEALING
                self._post_antes()
                self._emit(self._create_event(GameEventType.ANTES_POSTED))
                self._event_queue.append(GameEventType.ANTES_POSTED)

            case GameEventType.ANTES_POSTED:
                assert self.state.state_type == GameStateType.DEALING
                self.state.state_type = GameStateType.PRE_FLOP
                self._emit(self._create_event(GameEventType.BETTING_ROUND_STARTED))
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.PLAYER_ACTION_TAKEN:
                if self.state.is_betting_round_complete():
                    self._complete_betting_round()
                    self._emit(self._create_event(GameEventType.BETTING_ROUND_COMPLETED))
                    self._event_queue.append(GameEventType.BETTING_ROUND_COMPLETED)
                else:
                    self._advance_to_next_player()
                    self._take_action_from_current_player()
                    self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.BETTING_ROUND_COMPLETED:
                if len(self.state.get_players_in_hand()) == 1:
                    self.state.state_type = GameStateType.SHOWDOWN
                    self.state.street = Street.SHOWDOWN
                    self._emit(self._create_event(GameEventType.SHOWDOWN_STARTED))
                    self._handle_showdown()
                    self._emit(self._create_event(GameEventType.SHOWDOWN_COMPLETED))
                    self._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)
                else:
                    if self.state.state_type == GameStateType.PRE_FLOP:
                        self.state.state_type = GameStateType.FLOP
                        self.state.street = Street.FLOP
                        self._deal_flop()
                        self._emit(self._create_event(GameEventType.FLOP_DEALT))
                        self._event_queue.append(GameEventType.FLOP_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.state_type == GameStateType.FLOP:
                        self.state.state_type = GameStateType.TURN
                        self.state.street = Street.TURN
                        self._deal_turn()
                        self._emit(self._create_event(GameEventType.TURN_DEALT))
                        self._event_queue.append(GameEventType.TURN_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.state_type == GameStateType.TURN:
                        self.state.state_type = GameStateType.RIVER
                        self.state.street = Street.RIVER
                        self._deal_river()
                        self._emit(self._create_event(GameEventType.RIVER_DEALT))
                        self._event_queue.append(GameEventType.RIVER_DEALT)
                        self._advance_to_first_active_player()
                    elif self.state.state_type == GameStateType.RIVER:
                        self.state.state_type = GameStateType.SHOWDOWN
                        self.state.street = Street.SHOWDOWN
                        self._emit(self._create_event(GameEventType.SHOWDOWN_STARTED))
                        self._handle_showdown()
                        self._emit(self._create_event(GameEventType.SHOWDOWN_COMPLETED))
                        self._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)

            case (
                GameEventType.FLOP_DEALT
                | GameEventType.TURN_DEALT
                | GameEventType.RIVER_DEALT
            ):
                self._emit(self._create_event(GameEventType.BETTING_ROUND_STARTED))
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION_TAKEN)

            case GameEventType.SHOWDOWN_COMPLETED:
                self.state.state_type = GameStateType.HAND_COMPLETE
                self._emit(self._create_event(GameEventType.HAND_ENDED))
                self._event_queue.append(GameEventType.HAND_ENDED)

            case GameEventType.HAND_ENDED:
                self._log("Hand ended\n", logging.INFO, street_prefix=False)

                # eliminate players with zero stack
                eliminated_players = [
                    p for p in self.state.players if p.state.stack == 0
                ]
                for player in eliminated_players:
                    self._emit(
                        self._create_event(
                            GameEventType.PLAYER_ELIMINATED, player_id=player.id
                        )
                    )
                    self._log(
                        f"Player {player.name} has been eliminated from the game.",
                        logging.INFO,
                        street_prefix=False,
                    )
                    self._event_queue.append(GameEventType.PLAYER_ELIMINATED)
                
                # Remove eliminated players from the game
                self.state.players = [
                    p for p in self.state.players if p.state.stack > 0
                ]
                
                # remove eliminated players from the table
                for player in eliminated_players:
                    self._emit(
                        self._create_event(
                            GameEventType.PLAYER_LEFT, player_id=player.id
                        )
                    )
                    self._log(
                        f"Player {player.name} has left the table.",
                        logging.INFO,
                        street_prefix=False,
                    )
                    self._event_queue.append(GameEventType.PLAYER_LEFT)

                if len(self.state.players) < self.rules.dealing.min_players:
                    self._log(
                        "Not enough players to continue, ending game.", logging.INFO
                    )
                    self.state.state_type = GameStateType.GAME_OVER
                    self._event_queue.append(GameEventType.GAME_ENDED)
                else:
                    self._move_button()
                    
                    if self.state.hand_number >= self.max_hands:
                        self._log(
                            "Reached maximum number of hands, ending game.",
                            logging.INFO,
                            street_prefix=False,
                        )
                        self.state.state_type = GameStateType.GAME_OVER
                        self._event_queue.append(GameEventType.GAME_ENDED)
                    else:
                        self._start_new_hand()
                        self._event_queue.append(GameEventType.HAND_STARTED)

            case GameEventType.GAME_ENDED:
                self._log("Game ended", logging.INFO, street_prefix=False)
                self._emit(self._create_event(GameEventType.GAME_ENDED))

            case GameEventType.PLAYER_JOINED:
                if self.state.state_type == GameStateType.WAITING_FOR_PLAYERS:
                    if len(self.state.players) >= self.rules.dealing.min_players:
                        self.state.state_type = GameStateType.READY

            case GameEventType.PLAYER_LEFT:
                if len(self.state.players) < self.rules.dealing.min_players:
                    self.state.state_type = GameStateType.WAITING_FOR_PLAYERS
                    
            case GameEventType.PLAYER_ELIMINATED:
                pass

            case _:  # pragma: no cover
                raise ValueError(f"Unknown event: {event}")

    def _drain_event_queue(self) -> None:
        while self.step():
            pass

    def step(self) -> bool:
        """Process the next event in the queue."""
        if self.has_events():
            event = self._event_queue.popleft()
            self._handle_event(event)
            return True
        return False

    def has_events(self) -> bool:
        """Check if there are pending events in the queue."""
        return len(self._event_queue) > 0

    def _initialize_game(self) -> None:
        self.state.hand_number = 0
        self.state.button_position = self._find_first_button_position()

    def _start_new_hand(self) -> None:
        self.state.hand_number += 1

        self._log(
            "=" * 30 + f" Hand {self.state.hand_number} " + "=" * 30 + "\n",
            logging.INFO,
            street_prefix=False,
        )

        if len(self.state.players) < self.rules.dealing.min_players:
            raise ValueError("Not enough players to start hand")

        self.state.deck = Deck.standard_deck(shuffle=True)
        self.state.community_cards = []
        self.state.pot = 0
        self.state.current_bet = 0
        self.state.last_raise_size = 0

        for player in self.state.players:
            player.state.current_bet = 0
            player.state.total_contributed = 0
            player.state.acted_this_street = False
            player.state.holding = None
            if player.state.stack > 0:
                player.state.state_type = PlayerStateType.ACTIVE

        self.state.street = Street.PRE_FLOP

    def _calculate_min_raise_amount(self) -> int:
        """Calculates the minimum extra chips the current player must add
        right now to complete a minimum raise.

        Important: What this function returns is NOT the amount the pot needs to raise by
        or raise to, but the amount the player must add on top of their current bet.
        """
        player = self.state.get_current_player()

        player_bet_before = player.state.current_bet
        old_table_bet = self.state.current_bet
        last_raise_size = self.state.last_raise_size

        min_raise_to = old_table_bet + last_raise_size
        min_raise_by = min_raise_to - player_bet_before

        return min_raise_by

    def _take_action_from_current_player(self) -> None:
        current_player = self.state.get_current_player()

        if (
            not current_player
            or current_player.state.state_type != PlayerStateType.ACTIVE
        ):
            return

        valid_actions = self._get_valid_actions(current_player)
        min_raise_amount = self._calculate_min_raise_amount()

        action: PlayerAction = current_player.decide_action(
            game=self,
            valid_actions=valid_actions,
            min_raise_amount=min_raise_amount,
            call_amount=self.state.current_bet - current_player.state.current_bet,
            min_bet_amount=self.state.min_bet,
        )

        try:
            self._register_player_action(current_player, action)
        except Exception:
            self._log(
                f"Player {current_player.name} intended to take action: {action}.",
                logging.DEBUG,
            )
            self._log(
                f"Player {current_player.name} action invalid, folding.",
                logging.WARNING,
                exc_info=True,
            )
            warn(f"Player {current_player.name} action invalid, folding.")
            action = PlayerAction(
                player_id=current_player.id, action_type=ActionType.FOLD
            )
            self._register_player_action(current_player, action)

    def _deal_hole_cards(self) -> None:
        button = self.state.players[self.state.button_position]
        self._log(f"Dealing hole cards. Button: {button.name}", logging.INFO)
        for player in self.state.players:
            if player.state.state_type == PlayerStateType.ACTIVE:
                cards = self.state.deck.deal(self.rules.dealing.hole_cards)
                player.state.holding = Holding(cards=cards)

    def _post_blinds(self) -> None:
        """Post blinds with correct heads-up semantics (button posts SB in HU)."""
        num_players = len(self.state.players)
        min_num_players = self.rules.dealing.min_players
        if num_players < min_num_players:
            raise ValueError(f"Need at least {min_num_players} players to post blinds")

        # Heads-up special case:
        # - Button is SMALL blind
        # - Other player is BIG blind
        if num_players == 2:
            sb_index = self.state.button_position
            bb_index = (self.state.button_position + 1) % num_players
        else:
            # Multi-way:
            # - SB = left of button
            # - BB = left of SB
            sb_index = (self.state.button_position + 1) % num_players
            bb_index = (self.state.button_position + 2) % num_players

        # --- Small blind ---
        sb_player = self.state.players[sb_index]
        sb_amount = min(self.state.small_blind, sb_player.state.stack)
        sb_player.state.current_bet = sb_amount
        sb_player.state.total_contributed = sb_amount
        sb_player.state.stack -= sb_amount
        self.state.pot += sb_amount
        if sb_player.state.stack == 0:
            sb_player.state.state_type = PlayerStateType.ALL_IN

        self._log(
            f"Posting small blind of {sb_amount} by player {sb_player.name}. "
            f"Remaining stack: {sb_player.state.stack}",
            logging.INFO,
        )

        # --- Big blind ---
        bb_player = self.state.players[bb_index]
        bb_amount = min(self.state.big_blind, bb_player.state.stack)
        bb_player.state.current_bet = bb_amount
        bb_player.state.total_contributed = bb_amount
        bb_player.state.stack -= bb_amount
        self.state.pot += bb_amount
        if bb_player.state.stack == 0:
            bb_player.state.state_type = PlayerStateType.ALL_IN

        self._log(
            f"Posting big blind of {bb_amount} by player {bb_player.name}. "
            f"Remaining stack: {bb_player.state.stack}",
            logging.INFO,
        )

        # Table betting state
        # IMPORTANT: current_bet should reflect the actual posted BB amount if BB is short-stacked.
        self.state.current_bet = bb_amount
        self.state.min_bet = self.state.big_blind
        self.state.last_raise_size = (
            self.state.big_blind
        )  # preflop min raise increment is BB size

        # Next to act preflop:
        # - Heads-up: button (SB) acts first
        # - Multi-way: player left of BB acts first
        if num_players == 2:
            self.state.current_player_index = sb_index
        else:
            self.state.current_player_index = (bb_index + 1) % num_players

    def _post_antes(self) -> None:
        """Post antes for all active players."""
        if not self.state.ante or self.state.ante <= 0:
            return

        self._log("Posting antes.", logging.INFO)
        for player in self.state.players:
            if player.state.state_type == PlayerStateType.ACTIVE:
                ante_amount = min(self.state.ante, player.state.stack)
                player.state.current_bet += ante_amount
                player.state.total_contributed += ante_amount
                player.state.stack -= ante_amount
                self.state.pot += ante_amount
                if player.state.stack == 0:
                    player.state.state_type = PlayerStateType.ALL_IN

                self._log(
                    f"Player {player.name} posts ante of {ante_amount}. "
                    f"Remaining stack: {player.state.stack}",
                    logging.INFO,
                )

    def _calculate_raise_components(
        self, player: PlayerLike, chips_to_add: int
    ) -> tuple[int, int, int, int, int, bool]:
        """
        Returns:
            (player_add, player_bet_after, new_table_bet, call_part, raise_size, is_all_in)
        """
        stack_before = player.state.stack
        player_bet_before = player.state.current_bet
        old_table_bet = self.state.current_bet

        player_add = min(chips_to_add, stack_before)
        player_bet_after = player_bet_before + player_add

        # Important: table bet cannot decrease
        new_table_bet = max(old_table_bet, player_bet_after)

        call_needed = max(0, old_table_bet - player_bet_before)
        call_part = min(call_needed, player_add)

        # Amount the table bet increases by (0 if player didn't exceed old_table_bet)
        raise_size = new_table_bet - old_table_bet

        is_all_in = player_add >= stack_before

        return (
            player_add,
            player_bet_after,
            new_table_bet,
            call_part,
            raise_size,
            is_all_in,
        )

    def _reset_acted_flags_for_reopen(self, raiser_id: str) -> None:
        """
        Betting was reopened by a *full* raise (>= last_raise_size).
        Players get re-raise rights back, so we reset acted flags for ACTIVE players
        other than the raiser.
        """
        for p in self.state.players:
            if p.id != raiser_id and p.state.state_type == PlayerStateType.ACTIVE:
                p.state.acted_this_street = False

    def _register_player_action(self, player: PlayerLike, action: PlayerAction) -> None:
        action_type = action.action_type
        amount = action.amount or 0

        current_player = self.state.get_current_player()
        if not current_player or current_player.id != player.id:
            raise ValueError("Not this player's turn")

        if current_player.state.state_type != PlayerStateType.ACTIVE:
            raise ValueError("Player cannot act (folded or all-in)")

        valid_actions = self._get_valid_actions(current_player)
        if action_type not in valid_actions:
            raise ValueError(f"Invalid action: {action_type}")

        if action_type == ActionType.FOLD:
            current_player.state.state_type = PlayerStateType.FOLDED
            self._log(f"Player {current_player.name} folds.", logging.INFO)

        elif action_type == ActionType.CHECK:
            if current_player.state.current_bet != self.state.current_bet:
                raise ValueError("Cannot check when there is a bet to call")
            self._log(f"Player {current_player.name} checks.", logging.INFO)

        elif action_type == ActionType.CALL:
            call_amount = self.state.current_bet - current_player.state.current_bet
            actual_amount = min(call_amount, current_player.state.stack)
            current_player.state.current_bet += actual_amount
            current_player.state.total_contributed += actual_amount
            current_player.state.stack -= actual_amount
            self.state.pot += actual_amount

            if current_player.state.stack == 0:
                current_player.state.state_type = PlayerStateType.ALL_IN

            self._log(
                f"Player {current_player.name} calls with amount {actual_amount}. Remaining stack: {current_player.state.stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.BET:
            if self.state.current_bet > 0:
                raise ValueError("Cannot bet when there is already a bet")
            if amount < self.state.min_bet:
                raise ValueError(f"Bet must be at least {self.state.min_bet}")

            actual_amount = min(amount, current_player.state.stack)
            current_player.state.current_bet = actual_amount
            current_player.state.total_contributed += actual_amount
            current_player.state.stack -= actual_amount
            self.state.pot += actual_amount

            self.state.current_bet = actual_amount
            self.state.last_raise_size = actual_amount

            if current_player.state.stack == 0:
                current_player.state.state_type = PlayerStateType.ALL_IN

            # A bet opens action for others (everyone else must respond)
            self._reset_acted_flags_for_reopen(raiser_id=current_player.id)

            self._log(
                f"Player {current_player.name} bets amount {actual_amount}. Remaining stack: {current_player.state.stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.RAISE:
            old_table_bet = self.state.current_bet
            old_last_raise_size = self.state.last_raise_size

            (
                player_add,
                player_bet_after,
                new_table_bet,
                _,
                raise_size,
                is_all_in,
            ) = self._calculate_raise_components(current_player, amount)

            if raise_size == 0:
                raise ValueError("RAISE must increase the table bet")

            # Non-all-in raise must meet minimum raise size
            if not is_all_in and raise_size < old_last_raise_size:
                raise ValueError(
                    f"Raise size must be at least {old_last_raise_size} (attempted {raise_size})"
                )

            current_player.state.current_bet = player_bet_after
            current_player.state.total_contributed += player_add
            current_player.state.stack -= player_add
            self.state.pot += player_add
            self.state.current_bet = new_table_bet

            if is_all_in:
                current_player.state.state_type = PlayerStateType.ALL_IN

            # Reopen betting ONLY on a full raise (>= old_last_raise_size)
            reopens_betting = raise_size >= old_last_raise_size

            if reopens_betting:
                self.state.last_raise_size = raise_size
                self._reset_acted_flags_for_reopen(raiser_id=current_player.id)
            # else: short all-in raise does NOT reopen betting and must NOT reset flags

            self._log(
                f"Player {current_player.name} raises by {player_add} chips "
                f"to total bet {player_bet_after}. Remaining stack: {current_player.state.stack}.",
                logging.INFO,
            )

        elif action_type == ActionType.ALL_IN:
            old_table_bet = self.state.current_bet
            old_last_raise_size = self.state.last_raise_size

            chips_to_add = current_player.state.stack
            (
                player_add,
                player_bet_after,
                new_table_bet,
                _,
                raise_size,
                _,
            ) = self._calculate_raise_components(current_player, chips_to_add)

            current_player.state.current_bet = player_bet_after
            current_player.state.total_contributed += player_add
            current_player.state.stack = 0
            self.state.pot += player_add
            current_player.state.state_type = PlayerStateType.ALL_IN

            # If the all-in increases the table bet, update it
            if new_table_bet > old_table_bet:
                self.state.current_bet = new_table_bet

                # Reopen betting ONLY if raise_size meets minimum
                reopens_betting = raise_size >= old_last_raise_size
                if reopens_betting:
                    self.state.last_raise_size = raise_size
                    self._reset_acted_flags_for_reopen(raiser_id=current_player.id)
                # else: SHORT all-in -> DOES NOT reopen betting -> DO NOT reset acted flags

            self._log(
                f"Player {current_player.name} goes all-in with {player_add} chips.",
                logging.INFO,
            )

        # Mark actor as having acted
        current_player.state.acted_this_street = True
        self._log(
            f"Current pot: {self.state.pot} | Current bet: {self.state.current_bet}",
            logging.INFO,
        )

        # Emit player action event after all state mutations
        self._emit(
            self._create_event(
                GameEventType.PLAYER_ACTION_TAKEN,
                player_id=current_player.id,
                action=action,
            )
        )

    def _get_valid_actions(self, player: PlayerLike) -> list[ActionType]:
        actions = [ActionType.FOLD]

        call_amount = self.state.current_bet - player.state.current_bet

        if call_amount == 0:
            actions.append(ActionType.CHECK)
        else:
            if call_amount > 0 and player.state.stack > 0:
                actions.append(ActionType.CALL)

        if self.state.current_bet == 0 and player.state.stack >= self.state.min_bet:
            actions.append(ActionType.BET)

        if self.state.current_bet > 0:
            min_raise_increment = self.state.last_raise_size
            call_amount = self.state.current_bet - player.state.current_bet
            total_needed_for_min_raise = call_amount + min_raise_increment
            if player.state.stack >= total_needed_for_min_raise:
                actions.append(ActionType.RAISE)

        if player.state.stack > 0:
            actions.append(ActionType.ALL_IN)

        return actions

    def _advance_to_next_player(self) -> None:
        """
        Move to the next player who needs to act.

        IMPORTANT:
        A player may have already 'acted_this_street' but still needs to act again
        if they are facing a bet (player.current_bet < table.current_bet). This is
        what makes short all-ins work correctly without resetting acted flags.
        """
        start_index = self.state.current_player_index
        num_players = len(self.state.players)

        for _ in range(num_players):
            self.state.current_player_index = (
                self.state.current_player_index + 1
            ) % num_players
            
            # get current player
            p = self.state.players[self.state.current_player_index]

            # skip if not active
            if p.state.state_type != PlayerStateType.ACTIVE:
                continue

            facing_call = p.state.current_bet < self.state.current_bet
            needs_action = (not p.state.acted_this_street) or facing_call

            if needs_action:
                # we've found the next player who needs to act
                return

        # no players need to act, reset to start index
        self.state.current_player_index = start_index

    def _complete_betting_round(self) -> None:
        for player in self.state.players:
            player.state.current_bet = 0
            player.state.acted_this_street = False
        self.state.current_bet = 0
        self.state.last_raise_size = 0
        self._log("Betting round complete\n", logging.INFO)

    def _advance_to_first_active_player(self) -> None:
        self.state.current_player_index = (self.state.button_position + 1) % len(
            self.state.players
        )

        for _ in range(len(self.state.players)):
            player = self.state.players[self.state.current_player_index]
            if player.state.state_type == PlayerStateType.ACTIVE:
                return
            self.state.current_player_index = (
                self.state.current_player_index + 1
            ) % len(self.state.players)

    def _deal_flop(self) -> None:
        self.state.deck.deal(1)
        flop_cards = self.state.deck.deal(3)
        self.state.community_cards.extend(flop_cards)
        self._log(
            f"Dealt flop. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )

    def _deal_turn(self) -> None:
        self.state.deck.deal(1)
        turn_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(turn_card)
        self._log(
            f"Dealt turn. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )

    def _deal_river(self) -> None:
        self.state.deck.deal(1)
        river_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(river_card)
        self._log(
            f"Dealt river. Community cards: {[card.utf8() for card in self.state.community_cards]}",
            logging.INFO,
        )
        
    def _move_button(self) -> None:
        n_players = len(self.state.players)
        self.state.button_position = (self.state.button_position + 1) % n_players

    def _handle_showdown(self) -> None:
        players_in_hand = self.state.get_players_in_hand()

        if len(players_in_hand) == 1:
            winner = players_in_hand[0]
            winner.state.stack += self.state.pot
            self._log(
                f"Player {winner.name} wins {self.state.pot} from the pot.",
                logging.INFO,
            )
            self._emit(
                self._create_event(
                    GameEventType.POT_WON,
                    player_id=winner.id,
                    payload={"amount": self.state.pot},
                )
            )
        else:
            assert len(self.state.community_cards) == 5
            player_scores: list[tuple[PlayerLike, float]] = []
            for player in players_in_hand:
                if player.state.holding:
                    player_holding = " ".join(
                        card.utf8() for card in player.state.holding.cards
                    )
                    self._log(
                        f"Player {player.name} has holding {player_holding} at showdown,",
                        logging.INFO,
                    )
                    best_hand, best_hand_type, best_score = find_highest_scoring_hand(
                        private_cards=player.state.holding.cards,
                        community_cards=self.state.community_cards,
                        n_private=self.rules.showdown.hole_cards_required,
                    )
                    player_scores.append((player, best_score))
                    
                    self._emit(
                        self._create_event(
                            GameEventType.PLAYER_CARDS_REVEALED,
                            player_id=player.id,
                            payload={
                                "holding": [card.code() for card in player.state.holding.cards],
                                "best_hand": [card.code() for card in best_hand],
                                "best_hand_type": best_hand_type.name,
                                "best_score": best_score,
                            },
                        )
                    )
                    self._log(
                        (
                            f"Player {player.name} has hand {best_hand_type.name} with "
                            f"cards {[card.utf8() for card in best_hand]}"
                            f" (score: {best_score:.8g})"
                        ),
                        logging.INFO,
                    )

            player_scores.sort(key=lambda x: x[1], reverse=True)
            highest_score = player_scores[0][1]
            winners = [p for p, s in player_scores if s == highest_score]

            winners_sorted: list[PlayerLike] = sorted(
                winners, key=lambda p: p.state.seat if p.state.seat is not None else 0
            )

            pot_share = self.state.pot // len(winners)
            remainder = self.state.pot % len(winners)
            for i, winner in enumerate(winners_sorted):
                amount = pot_share + (1 if i < remainder else 0)
                winner.state.stack += amount
                self._log(
                    f"Player {winner.name} wins {amount} from the pot.", logging.INFO
                )
                self._emit(
                    self._create_event(
                        GameEventType.POT_WON,
                        player_id=winner.id,
                        payload={"amount": amount},
                    )
                )

        self._log("Showdown complete\n", logging.INFO)
