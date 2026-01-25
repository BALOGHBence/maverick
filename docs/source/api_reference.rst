API Reference
=============

This section provides detailed documentation for all classes and functions
in the Maverick library.

Core Classes
------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.game.Game
   maverick.state.GameState
   maverick.protocol.PlayerLike
   maverick.player.Player
   maverick.playerstate.PlayerState
   maverick.playeraction.PlayerAction

Card and Deck
-------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.card.Card
   maverick.deck.Deck

.. _players_api_reference:

Players
-------

There are two kinds of built-in players. The first kind is simple bots with very simple logic.
The second kind is player archetypes that implement common behavioral patterns of poker players.

Simple Bots
^^^^^^^^^^^

These bots have extremely simple logic and are mainly intended for testing and demonstration purposes.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.players.AggressiveBot
   maverick.players.CallBot
   maverick.players.FoldBot

Player Archetypes
^^^^^^^^^^^^^^^^^

The following player archetypes implement common behavioral patterns observed in poker players.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.players.ABCBot
   maverick.players.BullyBot
   maverick.players.FishBot
   maverick.players.GrinderBot
   maverick.players.GTOBot
   maverick.players.HeroCallerBot
   maverick.players.LooseAggressiveBot
   maverick.players.LoosePassiveBot
   maverick.players.ManiacBot
   maverick.players.ScaredMoneyBot
   maverick.players.SharkBot
   maverick.players.TightAggressiveBot
   maverick.players.TightPassiveBot
   maverick.players.TiltedBot
   maverick.players.WhaleBot

Events and Event Handling
-------------------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.events.GameEvent
   maverick.eventbus.EventBus

.. _rules_api_reference:

Rules
-----

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.rules.PokerRules
   maverick.rules.DealingRules
   maverick.rules.StakesRules
   maverick.rules.ShowdownRules

Hand Evaluation
---------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.hand.Hand
   maverick.holding.Holding

Utilities
---------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.utils.scoring.score_hand
   maverick.utils.holding_strength.estimate_holding_strength

Enumerations
------------

.. autosummary::
   :toctree: _autosummary

   maverick.enums.Suit
   maverick.enums.Rank
   maverick.enums.Street
   maverick.enums.HandType
   maverick.enums.PlayerStateType
   maverick.enums.GameStage
   maverick.enums.ActionType
   maverick.enums.GameEventType
