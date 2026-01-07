"""
Texas Hold'em Poker Game State Machine.

This module implements a complete Texas Hold'em poker game using a state machine
architecture. The game manages player actions, betting rounds, card dealing, and
pot distribution.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .card import Card
from .deck import Deck
from .enums import ActionType, GameEventType, GameStateType, PlayerState, Street
from .hand import Hand
from .holding import Holding
from .player import Player

__all__ = [
    "GameState",
    "GameEvent",
    "Game",
]


class GameEvent(BaseModel):
    """
    Represents an event that occurs during the game.

    Events are used to trigger state transitions and notify observers
    of significant occurrences in the game.
    """

    event_type: GameEventType
    player_id: Optional[str] = None
    action: Optional[ActionType] = None
    amount: Optional[int] = None
    cards: Optional[list[Card]] = None
    data: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


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
    Texas Hold'em Poker Game State Machine.

    This class implements a complete Texas Hold'em poker game using a state
    machine architecture. It manages game flow, player actions, betting rounds,
    and pot distribution.

    The game progresses through defined states:
    1. WAITING_FOR_PLAYERS: Game is waiting for players to join
    2. READY: Enough players to start
    3. DEALING: Dealing hole cards to players
    4. PRE_FLOP: First betting round (after hole cards)
    5. FLOP: Second betting round (after 3 community cards)
    6. TURN: Third betting round (after 4th community card)
    7. RIVER: Fourth betting round (after 5th community card)
    8. SHOWDOWN: Players reveal cards and winner is determined
    9. HAND_COMPLETE: Hand is over, preparing for next hand
    10. GAME_OVER: Game has ended

    Example:
        >>> game = Game(small_blind=10, big_blind=20)
        >>> game.add_player(Player(name="Alice", stack=1000))
        >>> game.add_player(Player(name="Bob", stack=1000))
        >>> game.start_game()
        >>> game.start_hand()
    """

    def __init__(
        self,
        small_blind: int = 10,
        big_blind: int = 20,
        min_players: int = 2,
        max_players: int = 9,
    ):
        """
        Initialize a new Texas Hold'em game.

        Args:
            small_blind: Amount of the small blind bet
            big_blind: Amount of the big blind bet
            min_players: Minimum number of players required to start
            max_players: Maximum number of players allowed at the table
        """
        self.min_players = min_players
        self.max_players = max_players
        self.state = GameState(small_blind=small_blind, big_blind=big_blind)
        self.event_history: list[GameEvent] = []
        self._state_handlers = self._initialize_state_handlers()

    def _initialize_state_handlers(self) -> dict:
        """Initialize the state transition handlers."""
        return {
            GameStateType.WAITING_FOR_PLAYERS: self._handle_waiting_for_players,
            GameStateType.READY: self._handle_ready,
            GameStateType.DEALING: self._handle_dealing,
            GameStateType.PRE_FLOP: self._handle_betting_round,
            GameStateType.FLOP: self._handle_betting_round,
            GameStateType.TURN: self._handle_betting_round,
            GameStateType.RIVER: self._handle_betting_round,
            GameStateType.SHOWDOWN: self._handle_showdown,
            GameStateType.HAND_COMPLETE: self._handle_hand_complete,
            GameStateType.GAME_OVER: self._handle_game_over,
        }

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

        self.state.players.append(player)

        # Update game state if we have enough players
        if len(self.state.players) >= self.min_players:
            self._transition_to(GameStateType.READY)

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

        self.state.players = [p for p in self.state.players if p.id != player_id]

        # Update game state
        if len(self.state.players) < self.min_players:
            self._transition_to(GameStateType.WAITING_FOR_PLAYERS)

    def start_game(self) -> None:
        """
        Start the game.

        Raises:
            ValueError: If not enough players to start
        """
        if self.state.state_type != GameStateType.READY:
            raise ValueError("Game is not ready to start")

        event = GameEvent(event_type=GameEventType.GAME_START)
        self._emit_event(event)
        self.start_hand()

    def start_hand(self) -> None:
        """Start a new hand."""
        if len(self.state.players) < self.min_players:
            raise ValueError("Not enough players to start hand")

        # Increment hand number
        self.state.hand_number += 1

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

        # Move button
        self.state.button_position = (self.state.button_position + 1) % len(
            self.state.players
        )
        self.state.dealer_index = self.state.button_position

        event = GameEvent(event_type=GameEventType.HAND_START)
        self._emit_event(event)

        # Transition to dealing state
        self._transition_to(GameStateType.DEALING)

    def _handle_waiting_for_players(self) -> None:
        """Handle WAITING_FOR_PLAYERS state."""
        # Wait for players to join
        pass

    def _handle_ready(self) -> None:
        """Handle READY state."""
        # Game is ready but not started yet
        pass

    def _handle_dealing(self) -> None:
        """Handle DEALING state - deal hole cards and post blinds."""
        # Deal hole cards to each player
        for player in self.state.players:
            if player.state == PlayerState.ACTIVE:
                cards = self.state.deck.deal(2)
                player.holding = Holding(cards=cards)

        event = GameEvent(event_type=GameEventType.DEAL_HOLE_CARDS)
        self._emit_event(event)

        # Post blinds
        self._post_blinds()

        # Transition to pre-flop
        self.state.street = Street.PRE_FLOP
        self._transition_to(GameStateType.PRE_FLOP)

        # Set first player to act (left of big blind)
        self.state.current_player_index = (self.state.button_position + 3) % len(
            self.state.players
        )

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

        # Big blind (left of small blind)
        bb_index = (self.state.button_position + 2) % num_players
        bb_player = self.state.players[bb_index]
        bb_amount = min(self.state.big_blind, bb_player.stack)
        bb_player.current_bet = bb_amount
        bb_player.total_contributed = bb_amount
        bb_player.stack -= bb_amount
        self.state.pot += bb_amount

        self.state.current_bet = self.state.big_blind
        self.state.min_bet = self.state.big_blind

        event = GameEvent(event_type=GameEventType.POST_BLINDS)
        self._emit_event(event)

    def _handle_betting_round(self) -> None:
        """Handle betting round states (PRE_FLOP, FLOP, TURN, RIVER)."""
        # This is called when entering a betting round state
        # The actual betting happens through player_action() calls
        pass

    def player_action(
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

        event = GameEvent(
            event_type=GameEventType.PLAYER_ACTION,
            player_id=player_id,
            action=action,
            amount=amount,
        )
        self._emit_event(event)

        # Move to next player
        self._advance_to_next_player()

        # Check if betting round is complete
        if self.state.is_betting_round_complete():
            self._complete_betting_round()

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

        # If we've cycled through all players, check betting round completion
        # This should be caught by is_betting_round_complete()

    def _complete_betting_round(self) -> None:
        """Complete the current betting round and transition to next state."""
        event = GameEvent(event_type=GameEventType.BETTING_ROUND_COMPLETE)
        self._emit_event(event)

        # Reset betting round state
        for player in self.state.players:
            player.current_bet = 0
            player.acted_this_street = False
        self.state.current_bet = 0

        # Check if we should go to showdown (only one player left)
        if len(self.state.get_players_in_hand()) == 1:
            self._transition_to(GameStateType.SHOWDOWN)
            return

        # Progress to next street
        if self.state.state_type == GameStateType.PRE_FLOP:
            self._deal_flop()
            self.state.street = Street.FLOP
            self._transition_to(GameStateType.FLOP)
        elif self.state.state_type == GameStateType.FLOP:
            self._deal_turn()
            self.state.street = Street.TURN
            self._transition_to(GameStateType.TURN)
        elif self.state.state_type == GameStateType.TURN:
            self._deal_river()
            self.state.street = Street.RIVER
            self._transition_to(GameStateType.RIVER)
        elif self.state.state_type == GameStateType.RIVER:
            self.state.street = Street.SHOWDOWN
            self._transition_to(GameStateType.SHOWDOWN)

        # Set first player to act (left of button)
        self.state.current_player_index = (self.state.button_position + 1) % len(
            self.state.players
        )
        # Find first active player
        self._advance_to_first_active_player()

    def _advance_to_first_active_player(self) -> None:
        """Move to the first active player from current position."""
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

        event = GameEvent(event_type=GameEventType.DEAL_FLOP, cards=flop_cards)
        self._emit_event(event)

    def _deal_turn(self) -> None:
        """Deal the turn (4th community card)."""
        self.state.deck.deal(1)  # Burn card
        turn_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(turn_card)

        event = GameEvent(event_type=GameEventType.DEAL_TURN, cards=[turn_card])
        self._emit_event(event)

    def _deal_river(self) -> None:
        """Deal the river (5th community card)."""
        self.state.deck.deal(1)  # Burn card
        river_card = self.state.deck.deal(1)[0]
        self.state.community_cards.append(river_card)

        event = GameEvent(event_type=GameEventType.DEAL_RIVER, cards=[river_card])
        self._emit_event(event)

    def _handle_showdown(self) -> None:
        """Handle SHOWDOWN state - determine winner and award pot."""
        players_in_hand = self.state.get_players_in_hand()

        if len(players_in_hand) == 1:
            # Only one player left, they win
            winner = players_in_hand[0]
            winner.stack += self.state.pot
            event = GameEvent(
                event_type=GameEventType.AWARD_POT,
                player_id=winner.id,
                amount=self.state.pot,
            )
            self._emit_event(event)
        else:
            # Multiple players - evaluate hands
            player_scores = []
            for player in players_in_hand:
                if player.holding:
                    # Find best 5-card hand
                    all_cards = player.holding.cards + self.state.community_cards
                    best_score = None
                    for hand in Hand.all_possible_hands(all_cards):
                        _, score = hand.score()
                        if best_score is None or score > best_score:
                            best_score = score
                    player_scores.append((player, best_score))

            # Find winner(s)
            player_scores.sort(key=lambda x: x[1], reverse=True)
            best_score = player_scores[0][1]
            winners = [p for p, s in player_scores if s == best_score]

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
                event = GameEvent(
                    event_type=GameEventType.AWARD_POT,
                    player_id=winner.id,
                    amount=amount,
                )
                self._emit_event(event)

        event = GameEvent(event_type=GameEventType.SHOWDOWN)
        self._emit_event(event)

        # Transition to hand complete
        self._transition_to(GameStateType.HAND_COMPLETE)

    def _handle_hand_complete(self) -> None:
        """Handle HAND_COMPLETE state - prepare for next hand or end game."""
        # Remove players with no chips
        self.state.players = [p for p in self.state.players if p.stack > 0]

        if len(self.state.players) < self.min_players:
            event = GameEvent(event_type=GameEventType.GAME_END)
            self._emit_event(event)
            self._transition_to(GameStateType.GAME_OVER)
        else:
            # Ready for next hand
            self._transition_to(GameStateType.READY)

    def _handle_game_over(self) -> None:
        """Handle GAME_OVER state."""
        # Game is over
        pass

    def _transition_to(self, new_state: GameStateType) -> None:
        """
        Transition to a new game state.

        Args:
            new_state: The state to transition to
        """
        old_state = self.state.state_type
        self.state.state_type = new_state

        # Call the appropriate state handler
        handler = self._state_handlers.get(new_state)
        if handler:
            handler()

    def _emit_event(self, event: GameEvent) -> None:
        """
        Emit a game event.

        Args:
            event: The event to emit
        """
        self.event_history.append(event)

    def get_game_info(self) -> dict:
        """
        Get current game information.

        Returns:
            Dictionary containing current game state information
        """
        return {
            "state": self.state.state_type.value,
            "street": self.state.street.value,
            "hand_number": self.state.hand_number,
            "pot": self.state.pot,
            "current_bet": self.state.current_bet,
            "community_cards": self.state.community_cards,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "stack": p.stack,
                    "state": p.state.value if p.state else None,
                    "current_bet": p.current_bet,
                }
                for p in self.state.players
            ],
        }
