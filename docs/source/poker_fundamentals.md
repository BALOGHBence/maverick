# Poker Fundamentals

Poker is a family of card games where players compete to win chips (or money). You win by either:

- having the best cards **when cards are revealed**, or
- getting everyone else to **give up** before the reveal.

```{note}
- Poker rules are largely universal, but small procedural details can vary by venue or online platform.  
- This document describes the most common modern conventions.
```

## The Basic Unit of Play: A “Hand”

In poker, play is divided into repeated rounds called **hands**.

A **hand** is one complete mini-game that starts when players put in the required starting bets and receive cards, and ends when:

- everyone but one player has given up, **or**
- the remaining players reveal their cards and a winner is chosen.

After a hand ends, the next hand begins and some roles rotate (explained below).

## What Are Players Trying to Win?

### The Pot

During a hand, players place chips into a shared pool called the **pot**.

- The pot is the “prize” for that hand.
- At the end of the hand, the winner receives the pot (or it is split in some variants).

### Two Ways to Win a Hand

1. **Win by being the last player remaining**  
   If all other players give up, the last player still in the hand wins the pot immediately.

2. **Win at the reveal (“showdown”)**  
   If multiple players stay until the end, they reveal their cards and the best hand (by fixed rankings) wins.

## The Table, Seats, and Turn Order

Poker is turn-based: players act one at a time. The order matters.

### The Dealer Button

A small marker called the **dealer button** (often just “the button”) indicates a reference position.

- The button moves one seat clockwise after each hand.
- Many rules use the button to decide **who acts first** and **who must put in starting chips**.

The button does **not** necessarily mean that person physically deals cards—especially in casinos and online games. It is mainly a turn-order marker.

## Starting Chips in the Pot: Forced Bets

Poker needs a reason for players to participate. Most games create this by requiring forced bets at the start of every hand.

### Blinds

In many popular poker games, two players must post blinds:

- **Small Blind (SB)**: a smaller forced bet
- **Big Blind (BB)**: a larger forced bet

These are posted before most players have a choice to act.

### Antes (Optional)

Some games also require an **ante**, a small forced bet paid by every player.

## Cards and Stages Within a Hand

Different poker variants use different dealing methods, but many modern games share a staged structure:

- cards are dealt,
- players have a chance to bet,
- more cards may be dealt,
- more betting may happen, and so on.

A stage with a chance to bet is called a **betting round** (also called a **street**).

### Example: Community-Card Games (Hold’em / Omaha)

In Texas Hold’em and Omaha, a hand commonly goes through:

1. **Pre-flop**  
   Players receive private cards (only they can see). Betting happens.

2. **Flop**  
   Three shared cards are placed face up in the center. Betting happens.

3. **Turn**  
   One more shared card is revealed. Betting happens.

4. **River**  
   One final shared card is revealed. Final betting happens.

5. **Showdown** (only if needed)  
   Remaining players reveal private cards to determine the winner.

The shared face-up cards are called **community cards** (or “the board”).

## What a Player Can Do on Their Turn

When it is your turn, you choose an action. The exact options can vary slightly by game and betting structure, but these are the core actions:

- **Fold (give up)**  
  You stop participating in this hand. You cannot win the pot, and you do not put in more chips.

- **Check (bet zero)**  
  You stay in the hand without adding chips **only if nobody has bet yet in this betting round**.

- **Call (match the bet)**  
  If someone has bet, you may pay the same amount to stay in the hand.

- **Bet (make the first wager)**  
  If nobody has bet yet this betting round, you may be the first to put chips in.

- **Raise (increase the wager)**  
  If someone has already bet, you may increase the amount others must match.

- **All-in (commit all remaining chips)**  
  You put all your remaining chips into the pot. This functions as a bet, call, or raise depending on the situation.

### A Simple Rule to Remember

- If there is **no bet** to match, you may **check** or **bet**.
- If there **is a bet**, you must **fold**, **call**, or **raise**.

## Common Poker Game Families (Variants)

Poker variants are commonly grouped by how cards are dealt and how a player forms their final 5-card hand.

### Community-Card Poker

Players share some face-up cards in the middle of the table.

#### Texas Hold’em

- Each player gets **2 private cards**.
- There are **5 community cards**.
- You make your best **5-card** poker hand using **any combination** of your 2 private cards and the 5 community cards.

#### Omaha

- Each player gets **4 private cards**.
- There are **5 community cards**.
- You must form your final hand using:
  - **exactly 2** of your private cards, and
  - **exactly 3** community cards.

Common sub-variants:

- **Pot-Limit Omaha (PLO)**: a betting structure where maximum bet sizes are tied to the pot.
- **Omaha Hi-Lo (8 or better)**: the pot may be split between the best high hand and a qualifying low hand.

### Draw Poker

Players start with a complete private set of cards and may replace (“draw”) some of them.

#### Five-Card Draw

- Each player receives **5 private cards**.
- Players may discard some cards and draw replacements (often once).
- Typically no community cards.

### Stud Poker

Players receive a mixture of face-up and face-down cards over multiple stages.

#### Seven-Card Stud

- No community cards.
- Each player receives **7 total cards** (some visible to everyone).
- Each player makes the best **5-card** hand.

### Mixed Games

Some formats rotate through multiple variants (for example, H.O.R.S.E.) to test broad skill.

## Betting Structures (How Big Can Bets Be?)

“Betting structure” means what sizes are allowed when betting or raising.

### Fixed-Limit

- Bet and raise sizes are fixed (for example, $10/$20 limit).
- Some places also cap how many raises can occur in a single betting round.

### No-Limit

- You may bet or raise any amount up to all your chips.
- This allows very large bets and dramatic all-in situations.

### Pot-Limit

- The maximum bet or raise is tied to the current size of the pot.
- Most famously used in Omaha.

## All-Ins and Side Pots (When Players Have Different Chip Stacks)

### What “All-In” Changes

If a player goes all-in and has fewer chips than another player’s bet:

- that all-in player can only win the part of the pot they “covered” with their chips.

### Side Pots

When some players can bet more than others, the game splits the pot into:

- a **main pot** (the part everyone can win), and
- one or more **side pots** (extra pots only eligible to players who contributed to them).

At the end, the game awards pots from smallest to largest, each among eligible players.

(target_hand_rankings)=
## Hand Rankings (Standard 5-Card Poker)

Most poker variants use the same ranking system for comparing 5-card hands.

From strongest to weakest:

1. **Royal Flush** (A-K-Q-J-10 all same suit)
2. **Straight Flush** (five in sequence, same suit)
3. **Four of a Kind**
4. **Full House**
5. **Flush** (same suit, not necessarily in sequence)
6. **Straight** (sequence, mixed suits allowed)
7. **Three of a Kind**
8. **Two Pair**
9. **One Pair**
10. **High Card**

### Tie-Breaking

- First compare the category (for example, any flush beats any straight).
- If the category matches, compare the relevant card ranks (pairs, highest card, kickers, etc.).
- **Suits do not break ties** in standard poker hand comparison.

## Glossary

- **Hand**: one complete round of play from start to finish.
- **Pot**: the chips players have wagered in the current hand.
- **Fold**: give up and stop participating in the current hand.
- **Check**: stay in without betting (only when no bet exists).
- **Call**: match the current bet.
- **Bet**: put chips in first during a betting round.
- **Raise**: increase an existing bet.
- **All-in**: put all remaining chips into the pot.
- **Community cards / Board**: shared face-up cards used by all players (in community-card games).
- **Showdown**: the moment remaining players reveal their cards to determine the winner.
- **Blind**: a forced bet (small blind or big blind).
- **Ante**: a forced bet paid by every player (if used).
- **Side pot**: an extra pot created when players go all-in for different amounts.

## How This Connects to Maverick

Maverick models community-card poker (Texas Hold’em rules by default) as a state-driven engine.

- Player decisions are represented by {class}`~maverick.playeraction.PlayerAction` with an{class}`~maverick.enums.ActionType`.
- Game flow, turn order, and betting rules are enforced by {class}`~maverick.game.Game`.

Some internal setup procedures may use deterministic tie-breakers (including suit order) for convenience—even though suits do not affect real hand strength.
