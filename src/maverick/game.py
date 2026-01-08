"""
Texas Hold'em Poker Game State Machine.

This module implements a complete Texas Hold'em poker game using a state machine
architecture. The game manages player actions, betting rounds, card dealing, and
pot distribution.
"""

from typing import Optional, Deque
from collections import deque
import logging

from pydantic import BaseModel, Field

from .card import Card
from .deck import Deck
from .enums import (
    ActionType,
    GameEventType,
    GameStateType,
    PlayerState,
    Street,
)
from .hand import Hand
from .holding import Holding
from .player import Player

__all__ = ["GameState", "Game"]


class GameState(BaseModel):
    """
    Represents the complete state of a Texas Hold'em game.

    This class encapsulates all information about the current state of the game,
    including players, community cards, pot, and betting information.
    """

    state_type: GameStateType = GameStateType.WAITING_FOR_PLAYERS
    street: Street = Street.PRE_FLOP
    players: list[Player] = Field(default_factory=list)
    active_players: list[int] = Field(default_factory=list)  # Indices of active players
    current_player_index: int = 0
    dealer_index: int = 0

    # Cards
    deck: Optional[Deck] = None
    community_cards: list[Card] = Field(default_factory=list)

    # Betting
    pot: int = 0
    current_bet: int = 0
    min_bet: int = 0
    small_blind: int = Field(default=10, ge=1)
    big_blind: int = Field(default=20, ge=1)

    # Hand tracking
    hand_number: int = 0
    button_position: int = 0

    class Config:
        arbitrary_types_allowed = True

    def get_active_players(self) -> list[Player]:
        """Return list of players who haven't folded and have chips."""
        return [
            p for p in self.players if p.state == PlayerState.ACTIVE and p.stack > 0
        ]

    def get_players_in_hand(self) -> list[Player]:
        """Return list of players still in the hand (not folded)."""
        return [p for p in self.players if p.state != PlayerState.FOLDED]

    def get_current_player(self) -> Optional[Player]:
        """Return the player whose turn it is."""
        if 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None

    def is_betting_round_complete(self) -> bool:
        """Check if the current betting round is complete."""
        active = self.get_active_players()

        # If only one player left, betting is complete
        if len(self.get_players_in_hand()) <= 1:
            return True

        # All players must have acted
        if not all(p.acted_this_street for p in active):
            return False

        # All active players must have equal bets or be all-in
        for player in active:
            if (
                player.state != PlayerState.ALL_IN
                and player.current_bet != self.current_bet
            ):
                return False

        return True


class Game:
    """
    Texas Hold'em Poker Game.

    Implements a Texas Hold'em poker game using an event-driven state machine.
    The game manages player actions, betting rounds, dealing, and pot distribution.

    Parameters
    ----------
    small_blind : int, default=10
        Amount of the small blind bet.
    big_blind : int, default=20
        Amount of the big blind bet.
    min_players : int, default=2
        Minimum number of players required to start.
    max_players : int, default=9
        Maximum number of players allowed at the table.
    max_hands : int, default=1000
        Maximum number of hands to play before stopping.

    Examples
    --------
    >>> game = Game(small_blind=10, big_blind=20, max_hands=40)
    >>> game.add_player(Player(name="Alice", stack=1000))
    >>> game.add_player(Player(name="Bob", stack=1000))
    >>> game.start()
    """

    def __init__(
        self,
        small_blind: int = 10,
        big_blind: int = 20,
        min_players: int = 2,
        max_players: int = 9,
        max_hands: int = 1000,
    ):
        self.min_players = min_players
        self.max_players = max_players
        self.max_hands = max_hands
        self.state = GameState(small_blind=small_blind, big_blind=big_blind)
        self._event_queue: Deque[GameEventType] = deque()
        self._logger = logging.getLogger(self.__class__.__name__)

    def _log(self, message: str, loglevel: int = logging.INFO) -> None:

        # ANSI colors (set NO_COLOR=1 to disable)
        color_map = {
            Street.PRE_FLOP: "\033[38;5;39m",   # blue
            Street.FLOP: "\033[38;5;34m",       # green
            Street.TURN: "\033[38;5;214m",      # orange
            Street.RIVER: "\033[38;5;196m",     # red
            Street.SHOWDOWN: "\033[38;5;201m",  # magenta
        }
        reset = "\033[0m"

        street = self.state.street
        street_name = street.name

        street_prefix = f"{color_map.get(street, '')}{street_name}{reset}"

        msg = f"{street_prefix} | {message}"
        self._logger.log(loglevel, msg)

    def add_player(self, player: Player) -> None:
        """
        Add a player to the game.

        Args:
            player: Player to add to the game

        Raises:
            ValueError: If table is full or game is in progress
        """
        if len(self.state.players) >= self.max_players:
            raise ValueError("Table is full")

        if self.state.state_type not in [
            GameStateType.WAITING_FOR_PLAYERS,
            GameStateType.READY,
        ]:
            raise ValueError("Cannot add players while game is in progress")

        # Assign seat number
        if player.seat is None:
            player.seat = len(self.state.players)

        # Set initial state
        player.state = PlayerState.ACTIVE
        player.acted_this_street = False

        # Add player to game
        self.state.players.append(player)

        # Update game state
        self._handle_event(GameEventType.PLAYER_JOINED)
        self._log(f"Player {player.name} joined the game.", logging.INFO)

    def remove_player(self, player_id: str) -> None:
        """
        Remove a player from the game.

        Args:
            player_id: ID of the player to remove

        Raises:
            ValueError: If player not found or game is in progress
        """
        if self.state.state_type not in [
            GameStateType.WAITING_FOR_PLAYERS,
            GameStateType.READY,
            GameStateType.HAND_COMPLETE,
        ]:
            raise ValueError("Cannot remove players while hand is in progress")

        # The player to remove
        player = [p for p in self.state.players if p.id == player_id]

        # Update player list
        self.state.players = [p for p in self.state.players if p.id != player_id]

        # Update game state
        self._handle_event(GameEventType.PLAYER_LEFT)
        self._log(f"Player {player.name} left the game.", logging.INFO)

    def start(self) -> None:
        """
        Starts the game.

        Kicks off the game's event loop, transitioning through hands until the game ends.
        """
        self._log("Game started.", logging.INFO)
        self._initialize_game()
        self._event_queue.append(GameEventType.GAME_STARTED)
        self._drain_event_queue()  # starts the event processing loop

    def _handle_event(self, event: GameEventType) -> None:
        match event:
            case GameEventType.GAME_STARTED:
                assert self.state.state_type == GameStateType.READY
                self.state.state_type = GameStateType.STARTED
                self._start_new_hand()
                self._event_queue.append(GameEventType.HAND_STARTED)

            case GameEventType.HAND_STARTED:
                assert self.state.state_type in [
                    GameStateType.STARTED,
                    GameStateType.HAND_COMPLETE,
                ]
                self.state.state_type = GameStateType.DEALING
                self._deal_hole_cards()
                self._event_queue.append(GameEventType.DEAL_HOLE_CARDS)

            case GameEventType.DEAL_HOLE_CARDS:
                assert self.state.state_type == GameStateType.DEALING
                self.state.state_type = GameStateType.PRE_FLOP
                self._post_blinds()
                self._event_queue.append(GameEventType.POST_BLINDS)

            case GameEventType.POST_BLINDS:
                assert self.state.state_type == GameStateType.PRE_FLOP
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION)

            case GameEventType.PLAYER_ACTION:
                if self.state.is_betting_round_complete():
                    self._complete_betting_round()
                    self._event_queue.append(GameEventType.BETTING_ROUND_COMPLETED)
                else:
                    self._advance_to_next_player()
                    self._take_action_from_current_player()
                    self._event_queue.append(GameEventType.PLAYER_ACTION)

            case GameEventType.BETTING_ROUND_COMPLETED:
                # Progress to next street
                if len(self.state.get_players_in_hand()) == 1:
                    # Only one player left -> go to showdown
                    self.state.state_type = GameStateType.SHOWDOWN
                    self.state.street = Street.SHOWDOWN
                    self._handle_showdown()
                    self._event_queue.append(GameEventType.SHOWDOWN)
                else:
                    if self.state.state_type == GameStateType.PRE_FLOP:
                        self.state.state_type = GameStateType.FLOP
                        self.state.street = Street.FLOP
                        self._deal_flop()
                        self._event_queue.append(GameEventType.DEAL_FLOP)
                    elif self.state.state_type == GameStateType.FLOP:
                        self.state.state_type = GameStateType.TURN
                        self.state.street = Street.TURN
                        self._deal_turn()
                        self._event_queue.append(GameEventType.DEAL_TURN)
                    elif self.state.state_type == GameStateType.TURN:
                        self.state.state_type = GameStateType.RIVER
                        self.state.street = Street.RIVER
                        self._deal_river()
                        self._event_queue.append(GameEventType.DEAL_RIVER)
                    elif self.state.state_type == GameStateType.RIVER:
                        self.state.state_type = GameStateType.SHOWDOWN
                        self.state.street = Street.SHOWDOWN
                        self._handle_showdown()
                        self._event_queue.append(GameEventType.SHOWDOWN)

                self._advance_to_first_active_player()

            case GameEventType.DEAL_FLOP:
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION)

            case GameEventType.DEAL_TURN:
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION)

            case GameEventType.DEAL_RIVER:
                self._take_action_from_current_player()
                self._event_queue.append(GameEventType.PLAYER_ACTION)

            case GameEventType.SHOWDOWN:
                self.state.state_type = GameStateType.HAND_COMPLETE
                self._event_queue.append(GameEventType.HAND_ENDED)

            case GameEventType.HAND_ENDED:
                self.state.players = [p for p in self.state.players if p.stack > 0]

                # Check if we have enough players to continue
                active_players = [p for p in self.state.players if p.stack > 0]
                if len(self.state.players) < self.min_players:
                    self._log("Not enough players to continue, ending game.", logging.INFO)
                    self.state.state_type = GameStateType.GAME_OVER
                    self._event_queue.append(GameEventType.GAME_ENDED)
                else:
                    # Move dealer/button position
                    n_players = len(self.state.players)
                    self.state.button_position = (
                        self.state.button_position + 1
                    ) % n_players
                    self.state.dealer_index = self.state.button_position

                    # Ready for next hand
                    if self.state.hand_number >= self.max_hands:
                        self._log(
                            "Reached maximum number of hands, ending game.", logging.INFO
                        )
                        self.state.state_type = GameStateType.GAME_OVER
                        self._event_queue.append(GameEventType.GAME_ENDED)
                    else:
                        self._start_new_hand()
                        self._event_queue.append(GameEventType.HAND_STARTED)

            case GameEventType.GAME_ENDED:
                self._log("Game ended", logging.INFO)

            case GameEventType.PLAYER_JOINED:
                if self.state.state_type == GameStateType.WAITING_FOR_PLAYERS:
                    if len(self.state.players) >= self.min_players:
                        self.state.state_type = GameStateType.READY

            case GameEventType.PLAYER_LEFT:
                if len(self.state.players) < self.min_players:
                    self.state.state_type = GameStateType.WAITING_FOR_PLAYERS

            case _:
                raise ValueError(f"Unknown event: {event}")

    def _drain_event_queue(self) -> None:
        """Process all queued events."""
        while self._event_queue:
            event = self._event_queue.popleft()
            self._handle_event(event)

    def _initialize_game(self) -> None:
        self.state.hand_number = 0

    def _start_new_hand(self) -> None:
        """Start a new hand."""
        # Increment hand number
        self.state.hand_number += 1

        self._log(f"Starting hand #{self.state.hand_number}", logging.INFO)

        if len(self.state.players) < self.min_players:
            raise ValueError("Not enough players to start hand")

        # Reset deck
        self.state.deck = Deck.standard_deck(shuffle=True)
        self.state.community_cards = []
        self.state.pot = 0
        self.state.current_bet = 0

        # Reset players
        for player in self.state.players:
            player.current_bet = 0
            player.total_contributed = 0
            player.acted_this_street = False
            player.holding = None
            if player.stack > 0:
                player.state = PlayerState.ACTIVE

    def _take_action_from_current_player(self) -> None:
        current_player = self.state.get_current_player()

        # Skip if no current player or player cannot act
        if not current_player or current_player.state != PlayerState.ACTIVE:
            return

        # Get valid actions and min raise
        valid_actions = self._get_valid_actions(current_player)
        min_raise = self.state.current_bet + self.state.min_bet

        # Ask player to decide
        action, amount = current_player.decide_action(
            self.state, valid_actions, min_raise
        )

        self._log(
            f"Player {current_player.name} decided to {action.name} with amount {amount}",
            logging.INFO,
        )

        # Execute the action
        # (player_action automatically advances to next player and transitions states)
        try:
            self._register_player_action(current_player.id, action, amount)
        except ValueError:
            # Fallback: fold
            self._log(
                f"Player {current_player.name} action invalid, folding.",
                logging.WARNING,
            )
            self._register_player_action(current_player.id, ActionType.FOLD, 0)

    def _deal_hole_cards(self) -> None:
        """Deal hole cards and post blinds."""
        self._log("Dealing hole cards", logging.INFO)
        for player in self.state.players:
            if player.state == PlayerState.ACTIVE:
                cards = self.state.deck.deal(2)
                player.holding = Holding(cards=cards)

    def _post_blinds(self) -> None:
        """Post small and big blinds."""
        num_players = len(self.state.players)

        # Small blind (left of button)
        sb_index = (self.state.button_position + 1) % num_players
        sb_player = self.state.players[sb_index]
        sb_amount = min(self.state.small_blind, sb_player.stack)
        sb_player.current_bet = sb_amount
        sb_player.total_contributed = sb_amount
        sb_player.stack -= sb_amount
        self.state.pot += sb_amount

        self._log(
            f"Posting small blind of {sb_amount} by player {sb_player.name}",
            logging.INFO,
        )

        # Big blind (left of small blind)
        bb_index = (self.state.button_position + 2) % num_players
        bb_player = self.state.players[bb_index]
        bb_amount = min(self.state.big_blind, bb_player.stack)
        bb_player.current_bet = bb_amount
        bb_player.total_contributed = bb_amount
        bb_player.stack -= bb_amount
        self.state.pot += bb_amount

        self._log(
            f"Posting big blind of {bb_amount} by player {bb_player.name}", logging.INFO
        )

        self.state.current_bet = self.state.big_blind
        self.state.min_bet = self.state.big_blind

        # Set next player to act (left of big blind)
        self.state.current_player_index = (self.state.button_position + 3) % len(
            self.state.players
        )

    def _register_player_action(
        self, player_id: str, action: ActionType, amount: int = 0
    ) -> None:
        """
        Process a player action.

        Args:
            player_id: ID of the player taking action
            action: Type of action (FOLD, CHECK, CALL, BET, RAISE, ALL_IN)
            amount: Amount for BET, RAISE actions

        Raises:
            ValueError: If action is invalid
        """
        current_player = self.state.get_current_player()
        if not current_player or current_player.id != player_id:
            raise ValueError("Not this player's turn")

        if current_player.state != PlayerState.ACTIVE:
            raise ValueError("Player cannot act (folded or all-in)")

        # Validate and process action
        valid_actions = self._get_valid_actions(current_player)
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}")

        if action == ActionType.FOLD:
            current_player.state = PlayerState.FOLDED
        elif action == ActionType.CHECK:
            if current_player.current_bet != self.state.current_bet:
                raise ValueError("Cannot check when there is a bet to call")
        elif action == ActionType.CALL:
            call_amount = self.state.current_bet - current_player.current_bet
            actual_amount = min(call_amount, current_player.stack)
            current_player.current_bet += actual_amount
            current_player.total_contributed += actual_amount
            current_player.stack -= actual_amount
            self.state.pot += actual_amount
            if current_player.stack == 0:
                current_player.state = PlayerState.ALL_IN
        elif action == ActionType.BET:
            if self.state.current_bet > 0:
                raise ValueError("Cannot bet when there is already a bet")
            if amount < self.state.min_bet:
                raise ValueError(f"Bet must be at least {self.state.min_bet}")
            actual_amount = min(amount, current_player.stack)
            current_player.current_bet = actual_amount
            current_player.total_contributed += actual_amount
            current_player.stack -= actual_amount
            self.state.pot += actual_amount
            self.state.current_bet = actual_amount
            if current_player.stack == 0:
                current_player.state = PlayerState.ALL_IN
            # Reset acted flags for other players
            for p in self.state.players:
                if p.id != player_id and p.state == PlayerState.ACTIVE:
                    p.acted_this_street = False
        elif action == ActionType.RAISE:
            min_raise = self.state.current_bet + self.state.min_bet
            if amount < min_raise:
                raise ValueError(f"Raise must be at least {min_raise}")
            # Amount is the total bet amount (not just the raise size)
            call_amount = self.state.current_bet - current_player.current_bet
            total_to_add = amount - current_player.current_bet
            actual_amount = min(total_to_add, current_player.stack)
            current_player.current_bet += actual_amount
            current_player.total_contributed += actual_amount
            current_player.stack -= actual_amount
            self.state.pot += actual_amount
            self.state.current_bet = current_player.current_bet
            if current_player.stack == 0:
                current_player.state = PlayerState.ALL_IN
            # Reset acted flags for other players
            for p in self.state.players:
                if p.id != player_id and p.state == PlayerState.ACTIVE:
                    p.acted_this_street = False
        elif action == ActionType.ALL_IN:
            actual_amount = current_player.stack
            current_player.current_bet += actual_amount
            current_player.total_contributed += actual_amount
            current_player.stack = 0
            self.state.pot += actual_amount
            current_player.state = PlayerState.ALL_IN
            if current_player.current_bet > self.state.current_bet:
                self.state.current_bet = current_player.current_bet
                # Reset acted flags for other players
                for p in self.state.players:
                    if p.id != player_id and p.state == PlayerState.ACTIVE:
                        p.acted_this_street = False

        current_player.acted_this_street = True

    def _get_valid_actions(self, player: Player) -> list[ActionType]:
        """Get list of valid actions for a player."""
        actions = [ActionType.FOLD]

        call_amount = self.state.current_bet - player.current_bet

        if call_amount == 0:
            actions.append(ActionType.CHECK)
        else:
            if player.stack >= call_amount:
                actions.append(ActionType.CALL)

        # Can bet if no one has bet yet
        if self.state.current_bet == 0 and player.stack >= self.state.min_bet:
            actions.append(ActionType.BET)

        # Can raise if there's a bet to raise
        min_raise_total = self.state.current_bet + self.state.min_bet
        total_needed_for_min_raise = min_raise_total - player.current_bet
        if self.state.current_bet > 0 and player.stack >= total_needed_for_min_raise:
            actions.append(ActionType.RAISE)

        # Can always go all-in if you have chips
        if player.stack > 0:
            actions.append(ActionType.ALL_IN)

        return actions

    def _advance_to_next_player(self) -> None:
        """Move to the next player who needs to act."""
        start_index = self.state.current_player_index
        num_players = len(self.state.players)

        # Find next active player
        for _ in range(num_players):
            self.state.current_player_index = (
                self.state.current_player_index + 1
            ) % num_players
            player = self.state.players[self.state.current_player_index]
            if player.state == PlayerState.ACTIVE and not player.acted_this_street:
                return

        # If we reach here, no players left to act
        self.state.current_player_index = start_index

    def _complete_betting_round(self) -> None:
        """Complete the current betting round."""
        # Reset betting round state
        for player in self.state.players:
            player.current_bet = 0
            player.acted_this_street = False
        self.state.current_bet = 0
        self._log("Betting round complete\n", logging.INFO)

    def _advance_to_first_active_player(self) -> None:
        """Move to the first active player from current position."""
        # Set first player to act (left of button)
        self.state.current_player_index = (self.state.button_position + 1) % len(
            self.state.players
        )

        for _ in range(len(self.state.players)):
            player = self.state.players[self.state.current_player_index]
            if player.state == PlayerState.ACTIVE:
                return
            self.state.current_player_index = (
                self.state.current_player_index + 1
            ) % len(self.state.players)

    def _deal_flop(self) -> None:
        """Deal the flop (3 community cards)."""
        self.state.deck.deal(1)  # Burn card
        flop_cards = self.state.deck.deal(3)
        self.state.community_cards.extend(flop_cards)
        self._log(f"Dealt flop. Community cards: {[card.utf8() for card in self.state.community_cards]}", logging.INFO)

    def _deal_turn(self) -> None:
        """Deal the turn (4th community card)."""
        self.state.deck.deal(1)  # Burn card
        turn_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(turn_card)
        self._log(f"Dealt turn. Community cards: {[card.utf8() for card in self.state.community_cards]}", logging.INFO)

    def _deal_river(self) -> None:
        """Deal the river (5th community card)."""
        self.state.deck.deal(1)  # Burn card
        river_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(river_card)
        self._log(f"Dealt river. Community cards: {[card.utf8() for card in self.state.community_cards]}", logging.INFO)

    def _handle_showdown(self) -> None:
        """Handle SHOWDOWN state - determine winner and award pot."""
        players_in_hand = self.state.get_players_in_hand()

        if len(players_in_hand) == 1:
            # Only one player left, they win
            winner = players_in_hand[0]
            winner.stack += self.state.pot

            self._log(
                f"Player {winner.name} wins the pot of {self.state.pot} by default (all others folded).",
                logging.INFO,
            )
        else:
            # Multiple players - evaluate hands
            assert len(self.state.community_cards) == 5
            player_scores = []
            for player in players_in_hand:
                if player.holding:
                    # Find best 5-card hand
                    best_score = None
                    for hand in Hand.all_possible_hands(
                        player.holding.cards, self.state.community_cards
                    ):
                        _, score = hand.score()
                        if (best_score is None) or (score > best_score):
                            best_score = score
                    player_scores.append((player, best_score))

            # Find winner(s)
            player_scores.sort(key=lambda x: x[1], reverse=True)
            highest_score = player_scores[0][1]
            winners = [p for p, s in player_scores if s == highest_score]

            # Sort winners by seat position (closest to button gets remainder chips)
            winners_sorted = sorted(
                winners, key=lambda p: p.seat if p.seat is not None else 0
            )

            # Split pot among winners, distribute remainder chips to winners closest to button
            pot_share = self.state.pot // len(winners)
            remainder = self.state.pot % len(winners)
            for i, winner in enumerate(winners_sorted):
                # First 'remainder' winners get 1 extra chip
                amount = pot_share + (1 if i < remainder else 0)
                winner.stack += amount

                self._log(
                    f"Player {winner.name} wins {amount} from the pot.", logging.INFO
                )
