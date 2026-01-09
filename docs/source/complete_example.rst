Complete Game Example
=====================

This example demonstrates a full Texas Hold'em poker game with custom player implementations.
The code is based on the working example in ``sandbox/test_game.ipynb``.

Overview
--------

In this example, we'll:

1. Create three different custom player types with unique strategies
2. Set up a game with these players
3. Run a complete game session with multiple hands
4. The game engine handles all state transitions automatically

Setting Up Logging
-------------------

First, let's configure logging to see what's happening in the game:

.. code-block:: python

    from maverick import Game, Player, ActionType, GameState, Street
    from maverick.players import FoldBot
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Get log messages only from the Game class
    logging.getLogger().setLevel(logging.WARNING)  # Set root logger to WARNING
    logging.getLogger("Game").setLevel(logging.DEBUG)  # Only Game logs at DEBUG

Custom Player Implementations
------------------------------

CallBot - Passive Player
~~~~~~~~~~~~~~~~~~~~~~~~

A simple bot that always calls or checks, never raising:

.. code-block:: python
    
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

A bot that makes decisions based on game state and pot odds:

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
            if game_state.street == Street.PRE_FLOP:
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

Running the Complete Game
--------------------------

Here's the complete script that sets up and runs the game:

.. code-block:: python

    # Create game with blinds and maximum number of hands
    game = Game(small_blind=10, big_blind=20, max_hands=10)
    
    # Create and add players with different strategies
    players = [
        CallBot(id="p1", name="CallBot", stack=1000, seat=0),
        AggressiveBot(id="p2", name="AggroBot", stack=1000, seat=1),
        SmartBot(id="p3", name="SmartBot", stack=1000, seat=2),
        FoldBot(id="p4", name="FoldBot", stack=1000, seat=3),
    ]
    
    for player in players:
        game.add_player(player)
        
    # Start the game - this runs all hands automatically!
    game.start()

That's it! The :meth:`~maverick.game.Game.start` method runs the entire game automatically.
The game engine handles:

* Dealing cards
* Managing betting rounds
* Transitioning between streets (PRE_FLOP → FLOP → TURN → RIVER)
* Determining winners
* Awarding pots
* Rotating the dealer button
* Playing multiple hands until ``max_hands`` is reached

Expected Output
---------------

With logging enabled, you'll see detailed information about the game progression:

.. code-block:: text

    2025-01-09 10:30:15 [DEBUG] Game: Starting game with 4 players
    2025-01-09 10:30:15 [DEBUG] Game: Starting hand 1
    2025-01-09 10:30:15 [DEBUG] Game: Posting blinds - SB: CallBot ($10), BB: AggroBot ($20)
    2025-01-09 10:30:15 [DEBUG] Game: Dealing hole cards to 4 players
    2025-01-09 10:30:15 [DEBUG] Game: SmartBot checks
    2025-01-09 10:30:15 [DEBUG] Game: FoldBot folds
    2025-01-09 10:30:15 [DEBUG] Game: CallBot calls $10
    2025-01-09 10:30:15 [DEBUG] Game: AggroBot raises to $40
    2025-01-09 10:30:15 [DEBUG] Game: SmartBot folds
    2025-01-09 10:30:15 [DEBUG] Game: CallBot calls $30
    2025-01-09 10:30:15 [DEBUG] Game: Dealing flop: 3♠ 7♥ K♦
    2025-01-09 10:30:15 [DEBUG] Game: CallBot checks
    2025-01-09 10:30:15 [DEBUG] Game: AggroBot bets $40
    2025-01-09 10:30:15 [DEBUG] Game: CallBot calls $40
    2025-01-09 10:30:15 [DEBUG] Game: Dealing turn: Q♣
    ...

Learning from the Example
-------------------------

This example demonstrates several key concepts:

**Automatic Game Flow**
  Once you call :meth:`~maverick.game.Game.start`, the game engine handles everything
  automatically. It:
  
  * Requests actions from players via their ``decide_action()`` method
  * Validates and executes actions
  * Manages state transitions
  * Deals cards at appropriate times
  * Determines winners and awards pots
  * Continues to the next hand automatically

**Player Decision Making**
  Each player's ``decide_action()`` method receives:
  
  * ``game_state``: Complete game state (pot, bets, community cards, street, etc.)
  * ``valid_actions``: List of legal actions the player can take
  * ``min_raise``: Minimum amount required for a raise
  
  This separation allows players to implement any strategy without knowing internal game mechanics.

**Strategy Differences**
  The four bots demonstrate different playing styles:
  
  * **CallBot**: Passive, calls or checks whenever possible
  * **AggressiveBot**: Bets and raises frequently to apply pressure
  * **SmartBot**: Considers pot odds and street when deciding
  * **FoldBot**: Always folds (from ``maverick.players``)

**Game Configuration**
  The :class:`~maverick.game.Game` constructor accepts:
  
  * ``small_blind``: Small blind amount (default: 1)
  * ``big_blind``: Big blind amount (default: 2)
  * ``max_hands``: Maximum number of hands to play (default: None = unlimited)

Next Steps
----------

Try modifying the example to:

* Implement your own custom bot with a unique strategy
* Add hand strength evaluation using the :mod:`~maverick.scoring` module
* Track player statistics across hands
* Implement different game variants (short-deck, heads-up, etc.)
* Add tournament structures with increasing blinds
* Create a visual interface for the game

See :doc:`custom_players` for more details on player implementation and :doc:`api_reference`
for the complete API documentation.
See :doc:`custom_players` for more details on player implementation and :doc:`api_reference`
for the complete API documentation.
