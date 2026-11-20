---
myst:
  html_meta:
    description: "Introduction to the rules of poker, including betting rounds, positions, blinds and hand rankings."
---

# Poker Fundamentals

Poker is a family of card games in which players compete to win chips (or money). It comes in many variants: the most popular is undoubtedly *No-Limit Texas Hold'em*, followed by others such as *Omaha* and *Pineapple*, to name just a few.

This guide explains how Texas Hold'em works through a worked example, introducing the key terminology along the way.

```{note}
- Poker rules are largely universal, but small procedural details can vary by venue or online platform.  
- This document describes the most common modern conventions.
```

```{note}
You can follow the evolution of a Texas Hold'em game {doc}`here <user_guide/core_concepts>`.
```

## How it Starts

Texas Hold'em is typically played by 2 to 10 players, with a strict mathematical limit of 22 players using a single standard 52-card **deck**. While the game is structurally flexible, different player counts completely change the pace, strategy, and dynamics of the table. In practice, if there are more than 10 players, the game starts at multiple tables, and the tables merge at some point, after a sufficient amount of palyers having been eliminated.

```{tip}
Before the game starts, remove the jokers and count the cards to make sure all 52 are there.
```

### Dealing the Chips

The game starts with handing out an equal amounf of **chips** for each player. Let say every player gets 5000 chips.

```{figure} _static/img/chips.jpeg
:alt: A starting stack of 5000 chips: four 1000 chips, one 500 chip, four 100 chips and four 25 chips
:align: center
:width: 80%

An example starting stack worth 5000 chips. Chips come in different denominations, usually told apart by colour.
```

```{note}
Yes, the stacks have 5 chips while the labels say 4. The image is AI-generated, and AI apparently can't count chips either. Consider it a free lesson: always count your opponent's stack yourself.
```

### Selecting the First Dealer

Unless you are playing in a casino or a tournament with a professional dealer, players take turns dealing the cards, so someone has to go first. To decide who, an unsung hero deals everyone a single card, face up (there is nothing to hide yet). Whoever gets the highest card becomes the first dealer. In case of a tie, the tied players are dealt another card, and this repeats until only one remains.

```{figure} _static/img/dealer_button.jpeg
:alt: The dealer button and the casual dealer.
:align: center
:width: 80%

The dealer button and the casual dealer.
```

```{important}
The identity of the dealer is not just about who deals the cards. The dealer gets to act last in most betting rounds, which is a huge positional advantage, because they can see what everyone else does first.
```

## How it Goes

A game consists of a series of rounds called **hands**, and every hand ends with at least one player collecting some well-earned chips. At the start of every hand, each player is dealt exactly 2 cards, which only they can see. Accidents do happen, of course, but you should never intentionally show your cards to an opponent.

```{admonition} Information
:class: note

The two private cards are often called the **holding**, **hole cards**, **pocket cards** or **starting hand**.
```

Each hand is further divided into betting rounds known as **streets**. The different streets have their own designated names: **pre-flop**, **flop**, **turn**, **river**.

```{figure} _static/img/game_structure.jpeg
:alt: The structure of a game.
:align: center
:width: 80%

The structure of a game.
```

### Pre-flop

The player cards are dealt, every player has seen theirs. Based on your cards, you should have an idea of your chances of winning the hand.

```{note}
There is going to be a section later about card strengths. Let's just agree for now that two aces, kings, or any two cards of the same figure is called a **pair** and having a pair is better than having two different figures at this point.
```

The next step is to bet an amount.

How much each player bets depends on their cards and playing style. Two seats next to the dealer are special, though: the **small blind**, directly to the dealer's left, and the **big blind**, directly to the left of the small blind. These players must put a fixed amount into the pot before anyone has seen their cards, so these are **forced bets** rather than choices. Confusingly, the amounts themselves are also called the **small blind** and the **big blind**, with the big blind usually twice the small blind. Blinds make sure there is always something in the **pot** worth fighting for. Without them, players could simply fold every hand until they were dealt a great one, and the game would drag on forever.

```{admonition} Information
:class: note

The **pot** is the pile of chips in the middle of the table that all bets go into, including the blinds. At the end of the hand, the winner takes the whole pot (or, in case of a tie, it is split between the winners).
```

```{note}
Some games also require an **ante**, a small forced bet paid by every player.
```

After the big blind, the other players don't need to bet if they don't want to. They have three options:

* to **FOLD**: give up the hand and put their cards away face down. They don't put any chips in the pot, but they also lose any chance of winning it.
* to **CALL**: match the current highest bet, which at this point is the big blind, to stay in the hand.
* to **RAISE**: increase the current highest bet. Everyone who wants to stay in the hand must then at least match the new amount.

Every next player has the same choices.

```{important}
When a player decides to raise, the amount they **raise by** must be at least as large as the previous bet or raise in the same betting round. Pre-flop, that means a raise must be at least one big blind.

For example, with blinds of 50 and 100, the smallest possible raise is to 200 (100 more than the big blind). If a player raises to 300 instead (200 more), anyone who wants to re-raise must go to at least 500.

The only exception is going **all-in**: a player can always bet all of their remaining chips, even if that is less than a full raise.
```

The action moves clockwise around the table. Pre-flop, it starts with the player to the left of the big blind and goes all the way around to the dealer. Then it comes back to the blinds, who act last because they have already put chips in the pot:

* The **small blind** has already paid half of the big blind, so to call, they only need to add the difference. If someone has raised in the meantime, the current bet may be well above the big blind, and they have to add more to stay in.
* The **big blind** acts last. If nobody has raised, their bet already matches the current bet, so they don't need to add anything. They can either **check** (stay in without betting more) or raise.

The betting round goes on until every player who hasn't folded has put the same amount into the pot. If someone raises, the action continues around the table, and everyone who already acted gets another chance to fold, call or raise again.

When the betting round is complete, the dealer deals 3 **community cards**.

```{admonition} Information
:class: note

The community cards are cards on the table that all players can see and use to complete their hand.
```

A simple rule to remember:

* If there is **no bet** to match, you may **CHECK**, **BET**, or go **ALL-IN**.
* If there **is a bet**, you must **FOLD**, **CALL**, **RAISE**, or go **ALL-IN**.

### Flop

At this point every player has 5 cards. 2 in their hands and 3 on the table. This completes the **hand**, which is the **best five-card hand** a player can make considering their private cards and all the community cards on the table.

Another betting round starts. The small and big blinds are not important from now on, except for the fact that their are the first players to act.

```{important}
This is the flip side of the dealer's positional advantage: the small blind is in the worst position. From the flop onwards, it acts first in every betting round, before it has seen what anyone else does. (If the small blind has folded, the first remaining player to the dealer's left takes on that role.) This doesn't mean though that this position can't be exploited ☝️.
```

The rules of this betting round are similar to that of the pre-flop, with some minor twists, coming from the lost significance of the small and big blinds. Now, each player has the following options:

* to **CHECK**: stay in the hand without putting any chips in the pot. This is only possible if nobody has bet yet in this betting round.
* to **BET**: put chips in the pot when nobody has bet yet in this betting round. The smallest possible bet is one big blind.
* to **CALL**: match the current highest bet to stay in the hand. This is only possible after someone has bet.
* to **RAISE**: increase the current highest bet, following the same minimum-raise rule as pre-flop. Everyone who wants to stay in the hand must then at least match the new amount.
* to **FOLD**: give up the hand, exactly as pre-flop. Folding while you could check for free is allowed, but it's never a good idea.
  
When the betting round is complete, the dealer deals 1 more community card.

### Turn

Now each player still in the game (haven't folded) is having 6 cards. 2 private cards and 4 community cards.

```{important}
The holding of every player is the best five-card hand, considering their private cards and all community cards. This could potentially mean 4 community cards and 1 private card.
```

The betting round here is the same as it was for the flop. Same rules, same options.

When the betting round is complete, the dealer deals 1 more community card.

### River

Now each player still in the game (haven't folded) is having 7 cards. 2 private cards and 5 community cards.

```{important}
The holding of every player is the best five-card hand, considering their private cards and all community cards. This could potentially mean 5 community cards and 0 private card.
```

The betting round here is the same as it was for the flop. Same rules, same options.

When the betting round is complete, the players who are still in the game reveal their cards during the showdown.

### Showdown

Following the same clockwise order as before, starting from the first active player on left of the dealer, the players reveal their cards. Obviusly, the first such player must reveal their cards. The next active players can decide to drop their cards without ever showing them. Needless to say, this is not a very wise move if they have a stronger hand.

Whoever has the strongest hand wins the current hand, and a new one starts. The dealer button moves in a clockwise fashion to the next player, and the next hand starts with the pre-flop.

The game continues until all but one player is eliminated, or the last two players agree to split the pot beteween them.

## Evaluating Hands

If and when it comes to showdown, the winner of the hand is decided by the strength of the best five-card hand of the active players.

(target_hand_rankings)=
### Hand Rankings

```{figure} _static/img/hand_rankings.jpeg
:alt: Hand rankings
:align: center
:width: 80%

Hand rankings for standard 5-Card Poker
```

### Tie-Breaking

* First compare the category (for example, any flush beats any straight).
* If the category matches, compare the relevant card ranks (pairs, highest card, kickers, etc.).
* **Suits do not break ties** in standard poker hand comparison.

## Remarks

1. Winning the showdown is not the only way to win. In general, a player can win in one of two possible ways:

   * **By being the last player remaining**: if all other players give up (fold), the last player still in the hand wins the pot immediately, regardless of street.
   * **At the showdown**: if multiple players stay until the end, they reveal their cards and the best hand (by fixed rankings) wins.

## Summary of Player Actions

When it is your turn, you choose an action. The exact options can vary slightly by game and betting structure, but these are the core actions:

| Action     | What it means                                                                                             | When you can do it                                                               |
| ---------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **FOLD**   | Give up the hand. You put in no more chips, but you can no longer win the pot.                            | Any time it is your turn.                                                        |
| **CHECK**  | Stay in the hand without adding any chips.                                                                | Only if nobody has bet yet in this betting round.                                |
| **BET**    | Make the first wager of the betting round.                                                                | Only if nobody has bet yet in this betting round.                                |
| **CALL**   | Put in enough chips to match the current highest bet and stay in the hand.                                | Only if someone has bet (pre-flop, the big blind counts as a bet).               |
| **RAISE**  | Increase the current highest bet. Everyone who wants to stay in must at least match it.                   | Only if someone has bet, and you raise by at least the previous bet or raise.    |
| **ALL-IN** | Put all your remaining chips into the pot. It counts as a bet, call or raise, depending on the situation. | Any time it is your turn, even if your chips fall short of a full call or raise. |

## Common Poker Game Families (Variants)

Poker variants are commonly grouped by how cards are dealt and how a player forms their final 5-card hand.

### Community-Card Poker

Players share some face-up cards in the middle of the table.

#### Texas Hold’em

* Each player gets **2 private cards**.
* There are **5 community cards**.
* You make your best **5-card** poker hand using **any combination** of your 2 private cards and the 5 community cards.

#### Omaha

* Each player gets **4 private cards**.
* There are **5 community cards**.
* You must form your final hand using:
  * **exactly 2** of your private cards, and
  * **exactly 3** community cards.

Common sub-variants:

* **Pot-Limit Omaha (PLO)**: a betting structure where maximum bet sizes are tied to the pot.
* **Omaha Hi-Lo (8 or better)**: the pot may be split between the best high hand and a qualifying low hand.

### Draw Poker

Players start with a complete private set of cards and may replace (“draw”) some of them.

#### Five-Card Draw

* Each player receives **5 private cards**.
* Players may discard some cards and draw replacements (often once).
* Typically no community cards.

### Stud Poker

Players receive a mixture of face-up and face-down cards over multiple stages.

#### Seven-Card Stud

* No community cards.
* Each player receives **7 total cards** (some visible to everyone).
* Each player makes the best **5-card** hand.

### Mixed Games

Some formats rotate through multiple variants (for example, H.O.R.S.E.) to test broad skill.

## Betting Structures (How Big Can Bets Be?)

“Betting structure” means what sizes are allowed when betting or raising.

### Fixed-Limit

* Bet and raise sizes are fixed (for example, $10/$20 limit).
* Some places also cap how many raises can occur in a single betting round.

### No-Limit

* You may bet or raise any amount up to all your chips.
* This allows very large bets and dramatic all-in situations.

### Pot-Limit

* The maximum bet or raise is tied to the current size of the pot.
* Most famously used in Omaha.

## All-INs and Side Pots (When Players Have Different Chip Stacks)

### What “ALL-IN” Changes

If a player goes all-in and has fewer chips than another player’s bet:

* that all-in player can only win the part of the pot they “covered” with their chips.

### Side Pots

When some players can bet more than others, the game splits the pot into:

* a **main pot** (the part everyone can win), and
* one or more **side pots** (extra pots only eligible to players who contributed to them).

At the end, the game awards pots from smallest to largest, each among eligible players.

## Glossary

| Term                | Aliases                                             | Meaning                                                                                           |
| ------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Hand**            | deal                                                | One complete round of play, from dealing the cards to awarding the pot.                           |
| **Hole cards**      | holding, pocket cards, starting hand, private cards | The cards dealt face down to each player, which only they can see.                                |
| **Street**          | betting round                                       | One of the betting rounds of a hand: pre-flop, flop, turn and river.                              |
| **Five-card hand**  | best five-card hand                                 | The strongest 5-card combination a player can make from their hole cards and the community cards. |
| **Pot**             | —                                                   | The chips players have wagered in the current hand.                                               |
| **Dealer**          | button, dealer button                               | The player who deals the cards and acts last after the flop. Marked by the dealer button.         |
| **FOLD**            | lay down, muck                                      | Give up and stop participating in the current hand.                                               |
| **CHECK**           | knock                                               | Stay in without betting (only when no bet exists).                                                |
| **CALL**            | flat call, smooth call                              | Match the current bet.                                                                            |
| **BET**             | open, lead                                          | Put chips in first during a betting round.                                                        |
| **RAISE**           | re-raise, 3-bet (when raising a raise)              | Increase an existing bet.                                                                         |
| **ALL-IN**          | shove, jam, push                                    | Put all remaining chips into the pot.                                                             |
| **Community cards** | board                                               | Shared face-up cards used by all players (in community-card games).                               |
| **Showdown**        | —                                                   | The moment remaining players reveal their cards to determine the winner.                          |
| **Blind**           | —                                                   | A forced bet posted before the cards are dealt (small blind or big blind).                        |
| **Ante**            | —                                                   | A forced bet paid by every player (if used).                                                      |
| **Side pot**        | —                                                   | An extra pot created when players go all-in for different amounts.                                |

## How This Connects to Maverick

Maverick models community-card poker (Texas Hold’em rules by default) as a state-driven engine.

* Player decisions are represented by {class}`~maverick.playeraction.PlayerAction` with an{class}`~maverick.enums.ActionType`.
* Game flow, turn order, and betting rules are enforced by {class}`~maverick.game.Game`.

Some internal setup procedures may use deterministic tie-breakers (including suit order) for convenience—even though suits do not affect real hand strength.
