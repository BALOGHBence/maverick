Player Archetypes
=================

Maverick includes a comprehensive collection of pre-built player archetypes that represent 
common behavioral patterns found in poker games. These archetypes can be used for testing, 
analysis, or as starting points for your own custom players.

Overview
--------

Player archetypes are pre-implemented player strategies that follow typical behavioral patterns
seen in poker games. Each archetype has distinct characteristics, strengths, and weaknesses.
All archetypes fully implement the :class:`~maverick.protocol.PlayerLike` protocol.

Using Archetypes
----------------

All archetype classes can be imported from ``maverick.players``:

.. code-block:: python

   from maverick import Game
   from maverick.players import TightAggressiveBot, LoosePassiveBot, ManiacBot
   from maverick.playerstate import PlayerState

   # Create a game with different archetypes
   game = Game(small_blind=10, big_blind=20)
   
   game.add_player(TightAggressiveBot(
       id="p1", 
       name="TAG Player", 
       state=PlayerState(stack=1000, seat=0)
   ))
   
   game.add_player(LoosePassiveBot(
       id="p2", 
       name="Calling Station", 
       state=PlayerState(stack=1000, seat=1)
   ))
   
   game.add_player(ManiacBot(
       id="p3", 
       name="Wild Player", 
       state=PlayerState(stack=1000, seat=2)
   ))
   
   game.start()

Fundamental Play-Style Archetypes
----------------------------------

These archetypes represent the four basic playing styles based on the combination of 
tight/loose (hand selection) and aggressive/passive (betting behavior).

**Tight-Aggressive (TAG)**
   Selective with starting hands, but bets and raises assertively when involved.
   
   - **Key Traits:** Discipline, strong value betting, positional awareness
   - **Strengths:** Consistently profitable, difficult to exploit
   - **Weaknesses:** Can become predictable if overly rigid
   - **Common At:** Winning regulars in cash games and tournaments

**Loose-Aggressive (LAG)**
   Plays a wide range of hands and applies relentless pressure.
   
   - **Key Traits:** Frequent raises, bluffs, creative lines
   - **Strengths:** Forces opponents into mistakes, dominates passive tables
   - **Weaknesses:** High variance, vulnerable to strong counter-strategies
   - **Common At:** Higher-stakes games, experienced online players

**Tight-Passive (Rock/Nit)**
   Plays very few hands and avoids big pots without premium holdings.
   
   - **Key Traits:** Folding, calling instead of raising
   - **Strengths:** Minimizes losses
   - **Weaknesses:** Misses value, extremely readable
   - **Common At:** Low-stakes live games

**Loose-Passive (Calling Station)**
   Plays too many hands and calls too often.
   
   - **Key Traits:** Limping, calling with weak or marginal hands
   - **Strengths:** Pays off strong hands
   - **Weaknesses:** Long-term losing style
   - **Common At:** Casual home games and low-stakes casinos

Psychological & Table-Dynamic Archetypes
-----------------------------------------

These archetypes represent players with distinctive psychological patterns or table dynamics.

**Maniac**
   Ultra-aggressive and unpredictable.
   
   - **Key Traits:** Constant betting and raising, massive bluffs
   - **Strengths:** Creates confusion and short-term chaos
   - **Weaknesses:** Burns chips rapidly over time
   - **Common At:** Short bursts in live and online play

**Tilted Player**
   Emotionally compromised after losses or bad beats.
   
   - **Key Traits:** Revenge plays, poor decision-making
   - **Strengths:** None while tilted
   - **Weaknesses:** Severe strategic leaks
   - **Common At:** All stakes, especially after big pots

**Bully**
   Uses stack size and intimidation to control the table.
   
   - **Key Traits:** Overbets, fast actions, pressure plays
   - **Strengths:** Exploits fearful or inexperienced opponents
   - **Weaknesses:** Overplays weak holdings
   - **Common At:** Deep-stack live games

Skill-Based / Modern Archetypes
--------------------------------

These archetypes represent modern, theoretically-informed playing styles.

**Grinder**
   Volume-oriented player focused on steady expected value.
   
   - **Key Traits:** Multitabling, consistent lines, bankroll discipline
   - **Strengths:** Reliable long-term profits
   - **Weaknesses:** Predictability, limited creativity
   - **Common At:** Online cash games

**GTO-Oriented Player**
   Strategy driven by game-theory optimal solutions.
   
   - **Key Traits:** Balanced ranges, mixed strategies
   - **Strengths:** Extremely difficult to exploit
   - **Weaknesses:** May underperform in soft, highly exploitative games
   - **Common At:** Mid-to-high stakes online

**Exploitative Player (Shark)**
   Adapts strategy dynamically based on opponent tendencies.
   
   - **Key Traits:** Strong reads, targeted adjustments
   - **Strengths:** Maximizes profit against weak players
   - **Weaknesses:** Requires constant attention and accurate reads
   - **Common At:** Live games and mixed-skill environments

Informal & Recreational Archetypes
-----------------------------------

These archetypes represent casual or recreational playing styles.

**Fish**
   A generally weak or inexperienced player who makes systematic, exploitable mistakes.
   
   - **Key Traits:** Plays too many hands, poor position awareness, excessive calling
   - **Strengths:** Unpredictable in the short term
   - **Weaknesses:** Negative expected value over time
   - **Common At:** Low-stakes online games, casual live games

**ABC Player**
   Straightforward, textbook poker with little deviation.
   
   - **Key Traits:** Plays by the book, predictable patterns
   - **Strengths:** Consistent, avoids major mistakes
   - **Weaknesses:** Predictable, exploitable by advanced players
   - **Common At:** Low to mid-stakes games

**Hero Caller**
   Calls big bets to "keep opponents honest," often incorrectly.
   
   - **Key Traits:** Calls large bets with marginal hands
   - **Strengths:** Occasionally catches bluffs
   - **Weaknesses:** Loses chips to value bets
   - **Common At:** All stakes, recreational players

**Scared Money**
   Plays too cautiously due to being under-rolled for the stakes.
   
   - **Key Traits:** Risk-averse, small bets, folds easily
   - **Strengths:** Survives longer
   - **Weaknesses:** Misses value opportunities, easily exploited
   - **Common At:** Players playing above their bankroll

**Whale**
   Extremely loose player willing to gamble large sums.
   
   - **Key Traits:** Plays almost every hand, makes huge bets
   - **Strengths:** Creates action, unpredictable
   - **Weaknesses:** Loses money quickly
   - **Common At:** High-stakes games, recreational millionaires

API Reference
-------------

For detailed information on each archetype's implementation, see the API documentation:

.. autosummary::
   :toctree: _autosummary
   :recursive:

   maverick.players.archetypes.TightAggressiveBot
   maverick.players.archetypes.LooseAggressiveBot
   maverick.players.archetypes.TightPassiveBot
   maverick.players.archetypes.LoosePassiveBot
   maverick.players.archetypes.ManiacBot
   maverick.players.archetypes.TiltedBot
   maverick.players.archetypes.BullyBot
   maverick.players.archetypes.GrinderBot
   maverick.players.archetypes.GTOBot
   maverick.players.archetypes.SharkBot
   maverick.players.archetypes.FishBot
   maverick.players.archetypes.ABCBot
   maverick.players.archetypes.HeroCallerBot
   maverick.players.archetypes.ScaredMoneyBot
   maverick.players.archetypes.WhaleBot

Creating Custom Archetypes
---------------------------

You can create your own archetypes by subclassing :class:`~maverick.player.Player` and implementing
the :meth:`~maverick.protocol.PlayerLike.decide_action` method. See the :doc:`custom_players` guide
for detailed instructions.

.. code-block:: python

   from maverick import Player, ActionType, GameState, PlayerAction

   class MyCustomArchetype(Player):
       """A custom playing style."""
       
       def decide_action(
           self, 
           game_state: GameState, 
           valid_actions: list[ActionType], 
           min_raise: int
       ) -> PlayerAction:
           """Implement your strategy here."""
           # Your custom logic
           if ActionType.CHECK in valid_actions:
               return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
           return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
