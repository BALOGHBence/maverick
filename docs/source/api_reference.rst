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

Card and Deck
-------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.card.Card
   maverick.deck.Deck

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
   maverick.enums.GameStateType
   maverick.enums.ActionType
   maverick.enums.GameEventType
