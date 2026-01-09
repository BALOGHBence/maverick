Creating Custom Players
=======================

This guide explains how to create custom player implementations for Texas Hold'em
poker games using the Maverick library.

Overview
--------

The Maverick library provides a flexible system for creating custom player
implementations. You can create players with different strategies, from simple
rule-based bots to sophisticated AI algorithms.

Player Protocol
---------------

All custom player implementations must conform to the :class:`~maverick.protocol.PlayerLike` protocol, which
defines the required interface for a player. The protocol ensures that your
custom player can interact with the game engine.

Required Attributes
~~~~~~~~~~~~~~~~~~~

Your custom player class must have the following attributes:

* ``id`` (Optional[str]): Unique identifier for the player
* ``name`` (Optional[str]): Display name for the player
* ``seat`` (Optional[int]): Seat number at the table (0-indexed)
* ``stack`` (int): Current chip count
* ``holding`` (Optional[Holding]): Current hole cards (None if no cards dealt)
* ``current_bet`` (int): Amount bet in current betting round
* ``total_contributed`` (int): Total amount contributed to pot this hand
* ``state`` (Optional[PlayerState]): Current player state (ACTIVE, FOLDED, ALL_IN)
* ``acted_this_street`` (bool): Whether player has acted in current betting round

Required Methods
~~~~~~~~~~~~~~~~

The most important method you must implement is:

.. code-block:: python

    def decide_action(
        self, 
        game_state: GameState, 
        valid_actions: list[ActionType], 
        min_raise: int
    ) -> tuple[ActionType, int]:
        """
        Decide what action to take given the current game state.

        Args:
            game_state: Current state of the game
            valid_actions: List of valid actions the player can take
            min_raise: Minimum amount for a raise action

        Returns:
            A tuple of (action_type, amount) where amount is relevant for
            BET, RAISE, CALL, and ALL_IN actions
        """
        ...

Using the Player Base Class
----------------------------

The library provides a ``Player`` class that implements all required attributes
as a Pydantic model. You can inherit from this class to create your custom player:

Basic Example
~~~~~~~~~~~~~

Here's a simple example of a custom player that always calls or checks:

.. code-block:: python

    from maverick import Player, ActionType, GameState
    
    class CallBot(Player):
        """A simple bot that always calls or checks."""
        
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
                return (ActionType.CALL, call_amount)
            else:
                return (ActionType.FOLD, 0)

Advanced Example: Aggressive Bot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a more sophisticated player that plays aggressively:

.. code-block:: python

    from maverick import Player, ActionType, GameState
    import random
    
    class AggressiveBot(Player):
        """An aggressive bot that frequently raises."""
        
        def __init__(self, aggression_factor: float = 0.7, **kwargs):
            super().__init__(**kwargs)
            self.aggression_factor = aggression_factor
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            """Make aggressive plays based on aggression factor."""
            
            # If we can raise and random chance based on aggression
            if ActionType.RAISE in valid_actions:
                if random.random() < self.aggression_factor:
                    # Raise between min_raise and 3x current bet
                    raise_amount = random.randint(
                        min_raise, 
                        min(game_state.current_bet * 3, self.stack)
                    )
                    return (ActionType.RAISE, raise_amount)
            
            # If we can bet (no one has bet yet)
            if ActionType.BET in valid_actions:
                if random.random() < self.aggression_factor:
                    bet_amount = random.randint(
                        game_state.min_bet,
                        min(game_state.big_blind * 3, self.stack)
                    )
                    return (ActionType.BET, bet_amount)
            
            # Otherwise call or check
            if ActionType.CALL in valid_actions:
                call_amount = game_state.current_bet - self.current_bet
                return (ActionType.CALL, call_amount)
            
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            
            # Last resort: fold
            return (ActionType.FOLD, 0)

Strategy-Based Example
~~~~~~~~~~~~~~~~~~~~~~~

Here's an example that uses hand strength to make decisions:

.. code-block:: python

    from maverick import Player, ActionType, GameState, Rank
    
    class StrategyBot(Player):
        """A bot that makes decisions based on hand strength."""
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            """Make decisions based on hand strength."""
            
            # Evaluate hand strength
            strength = self._evaluate_hand_strength(game_state)
            
            # Strong hand (high pair or better)
            if strength >= 0.7:
                if ActionType.RAISE in valid_actions:
                    raise_amount = min_raise * 2
                    return (ActionType.RAISE, raise_amount)
                elif ActionType.BET in valid_actions:
                    bet_amount = game_state.big_blind * 3
                    return (ActionType.BET, bet_amount)
                elif ActionType.CALL in valid_actions:
                    call_amount = game_state.current_bet - self.current_bet
                    return (ActionType.CALL, call_amount)
                elif ActionType.CHECK in valid_actions:
                    return (ActionType.CHECK, 0)
            
            # Medium hand
            elif strength >= 0.4:
                if ActionType.CHECK in valid_actions:
                    return (ActionType.CHECK, 0)
                elif ActionType.CALL in valid_actions:
                    # Only call if bet is reasonable
                    call_amount = game_state.current_bet - self.current_bet
                    if call_amount <= game_state.big_blind * 2:
                        return (ActionType.CALL, call_amount)
            
            # Weak hand - fold
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            return (ActionType.FOLD, 0)
        
        def _evaluate_hand_strength(self, game_state: GameState) -> float:
            """
            Evaluate hand strength on a scale from 0.0 to 1.0.
            
            This is a simplified evaluation. In practice, you would
            consider community cards, pot odds, and opponent behavior.
            """
            if not self.holding or len(self.holding.cards) < 2:
                return 0.0
            
            card1, card2 = self.holding.cards
            
            # Pair
            if card1.rank == card2.rank:
                # High pair is stronger
                if card1.rank.value >= Rank.JACK.value:
                    return 0.9
                elif card1.rank.value >= Rank.EIGHT.value:
                    return 0.7
                else:
                    return 0.5
            
            # High cards
            high_card = max(card1.rank.value, card2.rank.value)
            if high_card >= Rank.ACE.value:
                return 0.6
            elif high_card >= Rank.KING.value:
                return 0.5
            elif high_card >= Rank.TEN.value:
                return 0.4
            
            return 0.3

Accessing Game Information
---------------------------

The ``game_state`` parameter provides comprehensive information about the current
game situation:

Game State Attributes
~~~~~~~~~~~~~~~~~~~~~

* ``state_type``: Current state of the game (GameStateType enum)
* ``street``: Current betting round (PRE_FLOP, FLOP, TURN, RIVER)
* ``players``: List of all players in the game
* ``current_bet``: Current bet amount to call
* ``pot``: Total chips in the pot
* ``community_cards``: List of community cards dealt so far
* ``small_blind``: Small blind amount
* ``big_blind``: Big blind amount
* ``min_bet``: Minimum bet amount

Useful Methods
~~~~~~~~~~~~~~

* ``game_state.get_active_players()``: Get players who haven't folded and have chips
* ``game_state.get_players_in_hand()``: Get players still in the hand (not folded)
* ``game_state.get_current_player()``: Get the player whose turn it is
* ``game_state.is_betting_round_complete()``: Check if betting round is done

Example: Using Game Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def decide_action(
        self, 
        game_state: GameState, 
        valid_actions: list[ActionType], 
        min_raise: int
    ) -> tuple[ActionType, int]:
        """Make decisions based on game information."""
        
        # Check how many players are still in
        players_in_hand = len(game_state.get_players_in_hand())
        
        # Get pot size
        pot_size = game_state.pot
        
        # Check what street we're on
        street = game_state.street
        
        # See community cards (if any)
        community = game_state.community_cards
        
        # Make decision based on this information
        if players_in_hand == 2 and pot_size > self.stack:
            # Heads up for a big pot - play cautiously
            if ActionType.CHECK in valid_actions:
                return (ActionType.CHECK, 0)
            return (ActionType.FOLD, 0)
        
        # ... rest of decision logic

Using Custom Players in a Game
-------------------------------

Once you've created your custom player, you can use it in a game:

.. code-block:: python

    from maverick import Game
    
    # Create game
    game = Game(small_blind=10, big_blind=20)
    
    # Add custom players
    player1 = CallBot(id="p1", name="CallBot", stack=1000)
    player2 = AggressiveBot(
        id="p2", 
        name="AggroBot", 
        stack=1000,
        aggression_factor=0.8
    )
    player3 = StrategyBot(id="p3", name="StratBot", stack=1000)
    
    game.add_player(player1)
    game.add_player(player2)
    game.add_player(player3)
    
    # Start the game
    game.start_game()
    
    # Game loop
    while game.state.state_type != GameStateType.GAME_OVER:
        if game.state.state_type in [
            GameStateType.PRE_FLOP, 
            GameStateType.FLOP, 
            GameStateType.TURN, 
            GameStateType.RIVER
        ]:
            # Get current player
            current_player = game.state.get_current_player()
            
            if isinstance(current_player, Player) and hasattr(current_player, 'decide_action'):
                # Get valid actions
                valid_actions = game._get_valid_actions(current_player)
                min_raise = game.state.current_bet + game.state.min_bet
                
                # Let player decide
                action, amount = current_player.decide_action(
                    game.state, 
                    valid_actions, 
                    min_raise
                )
                
                # Execute action
                game.player_action(current_player.id, action, amount)

Best Practices
--------------

1. **Always Validate Actions**
   Make sure the action you return is in the ``valid_actions`` list.

2. **Handle All Cases**
   Always have a fallback action (usually FOLD or CHECK) in case your logic
   doesn't cover all scenarios.

3. **Consider Stack Size**
   Be aware of your chip stack when making bets or raises. Never try to bet
   more than you have.

4. **Use Game State Information**
   Take advantage of all the information available in the game state to make
   informed decisions.

5. **Test Your Player**
   Test your custom player thoroughly with different scenarios before using
   it in production.

6. **Consider Pot Odds**
   Advanced strategies should consider pot odds when deciding whether to call.

7. **Adapt to Opponents**
   Sophisticated players can track opponent behavior and adapt their strategy.

Advanced Topics
---------------

Tracking Opponent Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can maintain internal state to track opponent patterns:

.. code-block:: python

    class AdaptiveBot(Player):
        """A bot that adapts to opponent behavior."""
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.opponent_stats = {}  # Track opponent actions
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            # Update opponent stats based on game_state
            self._update_opponent_stats(game_state)
            
            # Make decisions based on opponent patterns
            # ...

Event Handling
~~~~~~~~~~~~~~

You can listen to game events to gather information:

.. code-block:: python

    class ObservantBot(Player):
        """A bot that observes game events."""
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.observed_actions = []
        
        def on_event(self, event: GameEvent):
            """React to game events."""
            if event.event_type == GameEventType.PLAYER_ACTION:
                self.observed_actions.append(event)
        
        def decide_action(
            self, 
            game_state: GameState, 
            valid_actions: list[ActionType], 
            min_raise: int
        ) -> tuple[ActionType, int]:
            # Use observed actions to inform decisions
            # ...

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**AttributeError: 'MyPlayer' object has no attribute 'X'**
  Make sure your custom player includes all required attributes from the protocol.

**ValueError: Invalid action**
  Ensure you're only returning actions that are in the ``valid_actions`` list.

**ValueError: Not enough chips**
  Check that your bet/raise amounts don't exceed the player's stack.

**Game hangs or loops infinitely**
  Make sure your ``decide_action`` method always returns a valid action.

Getting Help
~~~~~~~~~~~~

For more help with custom players:

* Check the API reference documentation
* Review the example implementations
* Examine the built-in ``Player`` class source code
* Test your player in isolated scenarios before full games
