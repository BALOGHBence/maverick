Complete Game Example
=====================

This example demonstrates a full Texas Hold'em poker game played from start
to finish with custom player implementations.

Overview
--------

In this example, we'll:

1. Create three different custom player types with unique strategies
2. Set up a game with these players
3. Play through multiple hands until the game ends
4. Track and display game events and outcomes

Custom Player Implementations
------------------------------

CallBot - Passive Player
~~~~~~~~~~~~~~~~~~~~~~~~

A simple bot that always calls or checks, never raising:

.. code-block:: python

    from maverick import Player, ActionType, GameState
    
    class CallBot(Player):
        """A passive bot that always calls or checks."""
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            """Always call or check if possible, otherwise fold."""
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            elif ActionType.CALL in valid_actions:
                call_amount = game_state.current_bet - self.current_bet
                if call_amount <= self.stack:
                    return (ActionType.CALL, call_amount)
            return (ActionType.FOLD, 0)

AggressiveBot - Aggressive Player
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A bot that likes to bet and raise:

.. code-block:: python

    class AggressiveBot(Player):
        """An aggressive bot that frequently bets and raises."""
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            """Bet or raise aggressively."""
            # Try to raise if possible
            if ActionType.RAISE in valid_actions:
                raise_amount = min_raise
                if raise_amount <= self.stack:
                    return (ActionType.RAISE, raise_amount)
            
            # Otherwise bet if possible
            if ActionType.BET in valid_actions:
                bet_amount = game_state.big_blind * 2
                if bet_amount <= self.stack:
                    return (ActionType.BET, bet_amount)
            
            # Call if we can't bet/raise
            if ActionType.CALL in valid_actions:
                call_amount = game_state.current_bet - self.current_bet
                if call_amount <= self.stack:
                    return (ActionType.CALL, call_amount)
            
            # Check if possible
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            
            # Otherwise fold
            return (ActionType.FOLD, 0)

SmartBot - Strategic Player
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A bot that makes decisions based on hand strength and pot odds:

.. code-block:: python

    class SmartBot(Player):
        """A strategic bot that considers hand strength."""
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            """Make strategic decisions based on game state."""
            # Simple strategy: aggressive early, cautious later
            pot_size = game_state.pot
            
            # On pre-flop, be selective
            if len(game_state.community_cards) == 0:
                if ActionType.CHECK in valid_actions:
                    return (ActionType.CHECK, 0)
                elif ActionType.CALL in valid_actions:
                    call_amount = game_state.current_bet - self.current_bet
                    # Only call small bets pre-flop
                    if call_amount <= game_state.big_blind * 3:
                        if call_amount <= self.stack:
                            return (ActionType.CALL, call_amount)
                return (ActionType.FOLD, 0)
            
            # Post-flop, consider pot size
            if ActionType.BET in valid_actions and pot_size < game_state.big_blind * 10:
                bet_amount = pot_size // 2
                if bet_amount <= self.stack and bet_amount >= game_state.min_bet:
                    return (ActionType.BET, bet_amount)
            
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            
            if ActionType.CALL in valid_actions:
                call_amount = game_state.current_bet - self.current_bet
                # Use pot odds to decide
                if call_amount <= pot_size // 3 and call_amount <= self.stack:
                    return (ActionType.CALL, call_amount)
            
            return (ActionType.FOLD, 0)

Complete Game Script
--------------------

Here's the complete script that runs a full game:

.. code-block:: python

    from maverick import Game, Player, ActionType, GameState, GameEventType, PlayerState, GameStateType
    
    # [Include all three bot classes from above]
    
    def print_game_state(game: Game):
        """Print current game state."""
        state = game.state
        print(f"\n{'='*60}")
        print(f"Game State: {state.state_type.value}")
        print(f"Street: {state.street.value if hasattr(state.street, 'value') else state.street}")
        print(f"Pot: ${state.pot}")
        print(f"Current Bet: ${state.current_bet}")
        
        if state.community_cards:
            cards_str = " ".join([f"{c.rank.name}{c.suit.value}" for c in state.community_cards])
            print(f"Community Cards: {cards_str}")
        
        print(f"\nPlayers:")
        for player in state.players:
            status = player.state.value if hasattr(player.state, 'value') else player.state
            holding = ""
            if player.holding and player.holding.cards:
                holding = " ".join([f"{c.rank.name}{c.suit.value}" for c in player.holding.cards])
            print(f"  {player.name:12} - Stack: ${player.stack:4} | "
                  f"Bet: ${player.current_bet:3} | Status: {status:8} | Cards: {holding}")
        print(f"{'='*60}\n")
    
    def print_event(event):
        """Print a game event."""
        if event.event_type == GameEventType.PLAYER_ACTION:
            action = event.action.value if hasattr(event.action, 'value') else event.action
            print(f"  → {event.data.get('player_name', 'Player')} {action}s "
                  f"${event.amount if event.amount else 0}")
        elif event.event_type == GameEventType.DEAL_FLOP:
            print(f"  → Flop dealt: {len(event.cards)} cards")
        elif event.event_type == GameEventType.DEAL_TURN:
            print(f"  → Turn dealt")
        elif event.event_type == GameEventType.DEAL_RIVER:
            print(f"  → River dealt")
        elif event.event_type == GameEventType.AWARD_POT:
            print(f"  → {event.data.get('player_name', 'Player')} wins ${event.amount}")
    
    def play_hand(game: Game):
        """
        Play a complete hand by processing player actions.
        
        The game automatically transitions through states (PRE_FLOP → FLOP → TURN → RIVER → SHOWDOWN)
        as betting rounds complete. We just need to keep getting actions from players until
        the hand reaches SHOWDOWN state.
        """
        max_actions = 1000  # Safety limit
        action_count = 0
        
        # Keep playing until hand reaches showdown
        while game.state.state_type not in [GameStateType.SHOWDOWN, GameStateType.HAND_COMPLETE]:
            action_count += 1
            if action_count > max_actions:
                print("⚠ Exceeded maximum actions per hand!")
                break
            
            current_player = game.state.get_current_player()
            
            # Skip if no current player or player cannot act
            if not current_player or current_player.state != PlayerState.ACTIVE:
                # Manually advance to next player
                game._advance_to_next_player()
                continue
            
            # Get valid actions and min raise
            valid_actions = game._get_valid_actions(current_player)
            min_raise = game.state.current_bet + game.state.min_bet
            
            # Ask player to decide
            action, amount = current_player.decide_action(
                game.state, valid_actions, min_raise
            )
            
            # Execute the action
            # (player_action automatically advances to next player and transitions states)
            try:
                game.player_action(current_player.id, action, amount)
            except ValueError as e:
                print(f"  ⚠ Invalid action from {current_player.name}: {e}")
                # Fallback: fold
                game.player_action(current_player.id, ActionType.FOLD, 0)
    
    def main():
        """Run a complete poker game."""
        print("Starting Texas Hold'em Poker Game")
        print("=" * 60)
        
        # Create game with blinds
        game = Game(small_blind=10, big_blind=20)
        
        # Create and add players with different strategies
        players = [
            CallBot(id="p1", name="CallBot", stack=1000, seat=0),
            AggressiveBot(id="p2", name="AggroBot", stack=1000, seat=1),
            SmartBot(id="p3", name="SmartBot", stack=1000, seat=2),
        ]
        
        for player in players:
            game.add_player(player)
        
        print(f"\nPlayers joined:")
        for p in players:
            print(f"  - {p.name} with ${p.stack}")
        
        # Start the game
        print("\n" + "=" * 60)
        print("Starting game...")
        game.start_game()
        
        hand_count = 0
        max_hands = 20  # Limit hands to keep example manageable
        
        # Play until not enough players or max hands reached
        while hand_count < max_hands:
            hand_count += 1
            print(f"\n{'#' * 60}")
            print(f"# HAND {hand_count}")
            print(f"{'#' * 60}")
            
            # Print initial state
            print_game_state(game)
            
            # Track events for this hand
            initial_event_count = len(game.event_history)
            
            # Play the hand (game auto-progresses through streets)
            play_hand(game)
            
            # Print events that occurred during the hand
            print("\nHand Events:")
            new_events = game.event_history[initial_event_count:]
            for event in new_events:
                print_event(event)
            
            # Print final state after hand
            print("\nHand Complete!")
            print_game_state(game)
            
            # Check if we have enough players to continue
            active_players = [p for p in game.state.players if p.stack > 0]
            if len(active_players) < 2:
                print(f"\n{'='*60}")
                print("GAME OVER - Not enough players with chips!")
                break
            
            # Start next hand
            try:
                game.start_hand()
            except Exception as e:
                print(f"Could not start new hand: {e}")
                break
        
        # Print final results
        print(f"\n{'='*60}")
        print("FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Hands played: {hand_count}")
        print(f"\nFinal chip counts:")
        sorted_players = sorted(game.state.players, key=lambda p: p.stack, reverse=True)
        for i, player in enumerate(sorted_players, 1):
            profit = player.stack - 1000
            profit_str = f"+${profit}" if profit > 0 else f"-${abs(profit)}"
            print(f"  {i}. {player.name:12} - ${player.stack:4} ({profit_str})")
        
        print(f"\nTotal events: {len(game.event_history)}")
        print("=" * 60)
    
    if __name__ == "__main__":
        main()

Running the Example
-------------------

To run this example:

1. Save the complete script to a file (e.g., ``poker_game.py``)
2. Make sure you have Maverick installed
3. Run the script:

.. code-block:: bash

   python poker_game.py

Expected Output
---------------

The script will output detailed information about each hand played:

* Current game state and pot size
* Community cards as they're dealt
* Each player's stack, current bet, and status
* Player actions (fold, check, call, bet, raise)
* Winner announcements and pot awards
* Final chip counts and profit/loss for each player

Example output snippet:

.. code-block:: text

    ============================================================
    # HAND 1
    ############################################################
    
    ============================================================
    Game State: pre_flop
    Street: 0
    Pot: $30
    Current Bet: $20
    
    Players:
      CallBot      - Stack: $990 | Bet: $10  | Status: active   | Cards: ...
      AggroBot     - Stack: $980 | Bet: $20  | Status: active   | Cards: ...
      SmartBot     - Stack: $1000| Bet: $0   | Status: active   | Cards: ...
    ============================================================
    
    Hand Events:
      → AggroBot raises $40
      → SmartBot calls $40
      → CallBot calls $30
      → Flop dealt: 3 cards
      → CallBot checks
      → AggroBot bets $40
      → SmartBot folds
      → CallBot calls $40
      → Turn dealt
      → CallBot checks
      → AggroBot bets $40
      → CallBot calls $40
      → River dealt
      → CallBot checks
      → AggroBot bets $40
      → CallBot calls $40
      → AggroBot wins $370

Learning from the Example
-------------------------

This example demonstrates several key concepts:

**Game Loop Architecture**
  The game uses a state machine but requires explicit action processing. The ``play_betting_round()``
  function drives the game by:
  
  1. Checking if the betting round is complete
  2. Getting the current player
  3. Calling the player's ``decide_action()`` method
  4. Executing the action via ``game.player_action()``
  5. Moving to the next player
  
  This pattern gives you full control over game flow and allows for features like
  timeouts, logging, or UI updates between actions.

**State Machine Flow**
  The game transitions through states (PRE_FLOP → FLOP → TURN → RIVER → SHOWDOWN)
  via explicit calls to ``game._transition_to()``. Each transition triggers appropriate
  handlers that deal cards and update game state.

**Player Decision Making**
  Each bot's ``decide_action`` method is called when it's their turn, receiving:
  
  * ``game_state``: Complete game state including pot, bets, community cards
  * ``valid_actions``: List of legal actions the player can take
  * ``min_raise``: Minimum amount required for a raise
  
  This separation allows players to implement any strategy without knowing internal game mechanics.

**Event Tracking**
  All game events are recorded in ``game.event_history``, allowing for replay and analysis.
  Events include player actions, cards dealt, and pot awards.

**Strategy Differences**
  The three bots demonstrate different playing styles:
  
  * CallBot: Passive, rarely folds
  * AggressiveBot: Bets and raises frequently
  * SmartBot: Considers pot size and position

**Game Management**
  The example shows proper game lifecycle management:
  
  1. Create game with blinds
  2. Add players
  3. Start game (deals first hand)
  4. Loop: play hand → check for winners → start next hand
  5. Display final results

Next Steps
----------

Try modifying the example to:

* Implement your own custom bot with a unique strategy
* Add more sophisticated decision-making (hand strength evaluation, position awareness)
* Track detailed statistics (win rate, aggression factor, etc.)
* Implement tournament structures with increasing blinds
* Add logging or visualization of game progression
* Add timeouts or user input for human players

See :doc:`custom_players` for more details on player implementation and :doc:`api_reference`
for the complete API documentation.
