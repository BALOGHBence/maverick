Texas Hold'em Poker Rules
=========================

Texas Hold'em is the most popular variant of poker. This document explains
the complete rules of the game as implemented in the Maverick library.

Game Overview
-------------

Texas Hold'em is a community card poker game where players attempt to make
the best five-card poker hand using a combination of their private hole cards
and shared community cards.

Basic Structure
---------------

Players and Seating
~~~~~~~~~~~~~~~~~~~

* A game requires a minimum of 2 players and supports up to 9 players
* Each player is assigned a seat at the table
* The dealer button rotates clockwise after each hand
* Positions are assigned relative to the dealer button

Table Positions
~~~~~~~~~~~~~~~

The position at the table determines the order of action:

**Button (Dealer)**
  The player with the dealer button. Acts last on all postflop betting rounds,
  providing maximum informational advantage.

**Small Blind (SB)**
  The player immediately to the left of the button. Posts a forced bet (the small
  blind) before cards are dealt. Acts first on all postflop betting rounds.

**Big Blind (BB)**
  The player to the left of the small blind. Posts a forced bet (the big blind)
  before cards are dealt. Acts last preflop but early on postflop streets.

**Under the Gun (UTG)**
  The first player to act preflop (after the blinds). This is the earliest
  position and has the least informational advantage.

**Middle Position (MP)**
  Positions between under-the-gun and the cutoff. Moderate informational advantage.

**Cutoff (CO)**
  The player immediately to the right of the button. A late position with
  significant informational advantage.

Hand Progression
----------------

Each hand of Texas Hold'em progresses through the following stages:

1. Posting Blinds
~~~~~~~~~~~~~~~~~

Before cards are dealt, two forced bets are posted:

* **Small Blind**: Posted by the player to the left of the button
* **Big Blind**: Posted by the player to the left of the small blind
* Typically, the big blind is twice the small blind

2. Dealing Hole Cards
~~~~~~~~~~~~~~~~~~~~~~

Each player receives two private cards (hole cards) dealt face-down. These
cards are known only to the player.

3. Pre-Flop Betting Round
~~~~~~~~~~~~~~~~~~~~~~~~~~

* First betting round occurs after hole cards are dealt
* Action begins with the player to the left of the big blind (under-the-gun)
* Players can fold, call the big blind, or raise
* The big blind acts last and can check if no one has raised

4. The Flop
~~~~~~~~~~~

* The dealer burns one card (discards it face-down)
* Three community cards are dealt face-up in the center of the table
* These cards are shared by all players
* A betting round occurs, starting with the first active player left of the button

5. The Turn
~~~~~~~~~~~

* The dealer burns another card
* A fourth community card is dealt face-up
* Another betting round occurs

6. The River
~~~~~~~~~~~~

* The dealer burns a final card
* A fifth and final community card is dealt face-up
* The final betting round occurs

7. Showdown
~~~~~~~~~~~

* If more than one player remains after the final betting round, players reveal
  their hands
* The player with the best five-card hand wins the pot
* Players make their best hand using any combination of their two hole cards
  and the five community cards

Betting Actions
---------------

During each betting round, players can take one of the following actions:

Fold
~~~~
Discard your hand and forfeit any chance of winning the pot. You cannot win
the current hand after folding.

Check
~~~~~
Pass the action to the next player without betting. Only available when there
is no bet to call. If all players check, the betting round ends.

Call
~~~~
Match the current bet to stay in the hand. Puts you at risk for the current
bet amount.

Bet
~~~
Be the first to put chips into the pot in a betting round. Sets the amount
other players must call. Minimum bet is typically the big blind amount.

Raise
~~~~~
Increase the current bet. Other players must match your raise to continue.
Minimum raise is typically the size of the previous bet or raise.

All-In
~~~~~~
Bet all remaining chips. A player who is all-in can win only the portion of
the pot they contributed to (main pot), while other players compete for any
remaining chips (side pots).

Betting Round Completion
~~~~~~~~~~~~~~~~~~~~~~~~

A betting round is complete when:

* All active players have acted
* All active players have either:
  
  * Folded
  * Called the current bet
  * Gone all-in

Hand Rankings
-------------

Hands are ranked from highest to lowest:

1. Royal Flush
~~~~~~~~~~~~~~
A, K, Q, J, 10, all of the same suit.

Example: A♠ K♠ Q♠ J♠ 10♠

2. Straight Flush
~~~~~~~~~~~~~~~~~
Five cards in sequence, all of the same suit.

Example: 9♥ 8♥ 7♥ 6♥ 5♥

3. Four of a Kind
~~~~~~~~~~~~~~~~~
Four cards of the same rank.

Example: K♠ K♥ K♦ K♣ 5♠

4. Full House
~~~~~~~~~~~~~
Three cards of one rank and two cards of another rank.

Example: A♠ A♥ A♦ 8♣ 8♠

5. Flush
~~~~~~~~
Five cards of the same suit, not in sequence.

Example: K♠ J♠ 9♠ 6♠ 2♠

6. Straight
~~~~~~~~~~~
Five cards in sequence, not all of the same suit.

Example: 9♥ 8♠ 7♦ 6♣ 5♥

7. Three of a Kind
~~~~~~~~~~~~~~~~~~
Three cards of the same rank.

Example: 7♠ 7♥ 7♦ K♣ 3♠

8. Two Pair
~~~~~~~~~~~
Two cards of one rank and two cards of another rank.

Example: A♠ A♥ 8♦ 8♣ 5♠

9. One Pair
~~~~~~~~~~~
Two cards of the same rank.

Example: 10♠ 10♥ K♦ 7♣ 4♠

10. High Card
~~~~~~~~~~~~~
When no other hand is made, the highest card plays.

Example: A♠ J♥ 9♦ 6♣ 3♠

Breaking Ties
~~~~~~~~~~~~~

When multiple players have the same hand type:

* **High Card**: Compare the highest card, then the next highest, and so on
* **Pair/Two Pair/Three of a Kind/Four of a Kind**: Compare the rank of the matched cards
* **Straight/Straight Flush**: Compare the highest card in the sequence
* **Flush**: Compare the highest card, then the next highest, and so on
* **Full House**: Compare the three-of-a-kind rank, then the pair rank

If hands are completely identical, the pot is split equally among the winners.

Winning the Pot
---------------

The pot is awarded to:

* The last player remaining if all others have folded
* The player(s) with the best hand at showdown

If multiple players have equal hands, the pot is split equally among them.

Special Cases
-------------

All-In and Side Pots
~~~~~~~~~~~~~~~~~~~~

When a player goes all-in with fewer chips than the current bet:

* A main pot is created containing chips that all players can win
* Side pots are created for additional betting among players with more chips
* A player can only win pots they contributed to

Running Out of Players
~~~~~~~~~~~~~~~~~~~~~~

The game ends when fewer than the minimum number of players (usually 2) remain
with chips.

Button Movement
~~~~~~~~~~~~~~~

The dealer button moves clockwise to the next player after each hand, even if
that player folded the previous hand.

Missed Blinds
~~~~~~~~~~~~~

In the current implementation, all players with chips post blinds when in position.
Players who run out of chips are removed from the game.
