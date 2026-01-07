.. maverick documentation master file, created by
   sphinx-quickstart on Tue Jan  6 19:43:00 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Maverick - Texas Hold'em Poker Library
=======================================

Maverick is a comprehensive Python library for Texas Hold'em poker. It provides
a complete game engine with a state machine architecture, making it easy to
create poker games, develop AI players, and analyze poker scenarios.

Features
--------

* **Complete Texas Hold'em Implementation**: Full game rules and mechanics
* **State Machine Architecture**: Clean separation of game states and transitions
* **Flexible Player System**: Protocol-based player interface for custom implementations
* **Hand Evaluation**: Built-in poker hand scoring and comparison
* **Event System**: Track all game events for analysis and replay
* **Well Documented**: Comprehensive documentation of rules and APIs

Quick Start
-----------

Install the library:

.. code-block:: bash

   uv sync

Create a simple game:

.. code-block:: python

   from maverick import Game, Player
   
   # Create a game
   game = Game(small_blind=10, big_blind=20)
   
   # Add players
   game.add_player(Player(id="p1", name="Alice", stack=1000))
   game.add_player(Player(id="p2", name="Bob", stack=1000))
   
   # Start playing
   game.start_game()

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   texas_holdem_rules
   custom_players
   complete_example
   api_reference

State Machine Architecture
--------------------------

The game engine is built as a state machine with the following states:

**WAITING_FOR_PLAYERS**
  Game is waiting for enough players to join.

**READY**
  Enough players have joined; game is ready to start.

**DEALING**
  Dealing hole cards to players and posting blinds.

**PRE_FLOP**
  First betting round after hole cards are dealt.

**FLOP**
  Second betting round after three community cards are dealt.

**TURN**
  Third betting round after the fourth community card is dealt.

**RIVER**
  Final betting round after the fifth community card is dealt.

**SHOWDOWN**
  Players reveal hands and the winner is determined.

**HAND_COMPLETE**
  Hand has ended; preparing for the next hand.

**GAME_OVER**
  Game has ended (not enough players with chips).

Creating Custom Players
-----------------------

Maverick uses a protocol-based system for player implementations. This allows you
to create custom players with any strategy you want:

.. code-block:: python

   from maverick import Player, ActionType, GameState
   
   class MyBot(Player):
       """A custom poker bot."""
       
       def decide_action(
           self, 
           game_state: GameState, 
           valid_actions: list[ActionType], 
           min_raise: int
       ) -> tuple[ActionType, int]:
           """Decide what action to take."""
           # Your strategy here
           if ActionType.CHECK in valid_actions:
               return (ActionType.CHECK, 0)
           return (ActionType.FOLD, 0)

See the :doc:`custom_players` guide for detailed instructions.

Game Events
-----------

The game engine emits events for all significant occurrences:

* ``GAME_START``: Game begins
* ``HAND_START``: New hand starts
* ``DEAL_HOLE_CARDS``: Hole cards dealt
* ``DEAL_FLOP``: Flop dealt
* ``DEAL_TURN``: Turn dealt
* ``DEAL_RIVER``: River dealt
* ``PLAYER_ACTION``: Player takes action
* ``BETTING_ROUND_COMPLETE``: Betting round ends
* ``SHOWDOWN``: Showdown occurs
* ``AWARD_POT``: Pot awarded to winner
* ``HAND_END``: Hand ends
* ``GAME_END``: Game ends

Access event history through ``game.event_history``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

