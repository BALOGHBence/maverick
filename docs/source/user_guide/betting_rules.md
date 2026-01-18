# Betting Rules - Implemented Semantics & Edge Cases

This document summarizes **the exact betting semantics implemented by this engine** where different poker engines sometimes diverge.

The goal is that **users of the library can predict behavior precisely**, especially around **minimum raises** and **all‑in edge cases**.

## Glossary

- **Street**: PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN
- **Button (BTN)**: Dealer position that rotates each hand.
- **Small Blind (SB)** and **Big Blind (BB)**: forced bets posted pre-flop.
- **Current bet (table bet)**: the amount players must match on the current street.
- **Player current bet**: how much a player has put in on the current street toward matching the table bet.
- **All-in**: player has committed all chips; they cannot take further actions.
- **Minimum raise size** (aka *min raise increment*): the minimum amount by which the table bet must increase for a raise to be “full”.

## Blind Posting & First-to-Act Order

### Multi-Way (3+ players)

- **SB** is the player **immediately left of the button**.
- **BB** is the player **immediately left of the SB**.
- **First to act pre-flop** is the player **left of the BB** (*UTG*).

### Heads-up (2 players) - Special Rules

In heads-up, rules differ from multi-way:

- **Button posts the Small Blind**
- The other player posts the Big Blind
- **Button acts first pre-flop**
- **Big blind acts first on all post-flop streets**

```{note}
**This engine implements the real heads-up rules above.** Many homegrown engines accidentally treat heads-up like 3+ players; this library **does not**.
```

## Action Semantics: BET vs RAISE vs CALL vs CHECK

### CHECK

- Allowed only if the player has already matched the current table bet:
  - `player.current_bet == table.current_bet`

### CALL

- Puts in exactly enough chips to match the current table bet *if possible*.
- If the player doesn’t have enough chips, they put in **their remaining stack** and become **ALL_IN**.

### BET

- Only allowed when there is no bet yet on this street:
  - `table.current_bet == 0`
- Must be at least `min_bet` (engine-defined, typically BB on post-flop in this codebase).
- A BET sets both:
  - `table.current_bet = bet_amount`
  - `last_raise_size = bet_amount` (first bet sets the min raise increment for the next raise)

### RAISE

```{danger}
It's extremely important to fully understand how raising works in poker and in this library in particular if you want to create custom players. When your bot decides to RAISE, it must also return the amount of chips associated with the action. If this amount is invalid (smaller then the minimum required), the engine will refuse the action and the player will be forced to fold.
```

In poker, when a player raises, they increase the current bet. The difference between the bet before and after the raise is called the **raise increment**. **The rule is: if the bet increases, the increment must be at least as large as the previous increment.** When the BB is posted, it establishes the initial increment (the BB amount itself). If the next player wants to RAISE, they must increase the bet by at least the BB amount. If their raise increment exceeds the BB, then subsequent raises must match or exceed that new increment.

```{important}
In this engine, `PlayerAction.amount` is **raise-by** / **chips-to-add** from stack,
not “raise-to”. It's NOT the value of the pot after the raise and it's NOT the increment either. It is the amount of chips the player puts to the table from their stack **on top of their current street contribution**. It is the value of the transaction from the player's stack to the pot.
```

Example (pre-flop, BB=20):

- Player has contributed 0 so far and faces `table.current_bet = 20`.
- `PlayerAction.amount = 40` means:
  - player adds 40 chips total
  - first 20 chips are the call portion
  - remaining 20 chips increase the table bet
  - resulting table bet becomes 40
  - raise size (increment) is 20

This also means that the next player who wants to raise must increase the table bet by at least 20 chips. This doesn't mean that they have to put in 20 chips from their stack. If their current bet is 0, then the minimum they have to put in from their stack is 60 (40 to call + 20 to raise), since the current table bet is 40.

```{note}
Many poker UIs speak “raise **to** X”, while internal engines often store “raise **by** Y”.  
This library explicitly uses **raise-by** for `PlayerAction.amount`.
```

#### An Important Edge Case: Short All-In RAISE

It might be that a player has enough chips to raise the bet, but not enough to raise the bet with the minimum amount required. In poker terminology, we call this a **short all-in**. In a situation like that

- The player **goes all-in**.
- Their **all-in** increases the table bet.
- **The action does not reopen betting for players who already acted.** Those players may FOLD or CALL, but they don't regain the right to RAISE.
- The players who haven't acted yet can FOLD, CALL or even RAISE, since they are still facing action for the first time.

## Betting Round Completion

A betting round is complete if **any** of these are true:

1. **Only one player remains in hand** (everyone else folded).
2. **No one can act** (all remaining players are ALL_IN).
3. Otherwise:
   - **All ACTIVE players** have acted since last reopen, **and**
   - **All ACTIVE players** have matched the table bet:
     - `player.current_bet == table.current_bet`

Notes:

- ALL_IN players are not required to match the table bet (they can’t add chips).
- Only **ACTIVE** players must satisfy the “acted + matched” conditions.

## What This Engine Does NOT Cover

- **Side pot construction** and distributing multiple side pots at showdown.
- **Bet sizing rules** beyond minimums (e.g., post-flop min bet conventions).
- **Re-raise rights** nuances for multi-way short all-ins and “cap” behavior.
- **Straddle** and other forced bets.
- **Dead blinds** when players enter/leave between hands.
- **Posting order adjustments** when seats are missing (e.g., button skipping empty seats).

## Practical Examples

### Example A - Short All-In Does NOT Reopen Betting

- BB = 20, last_raise_increment = 20
- Players A and B acted already and matched 20
- Player C goes all-in and increases table bet to 30 (raise_increment = 10)

Result:

- Table bet becomes 30
- `last_raise_increment` stays 20
- A and B **must act again** only to call the extra 10 (or fold)
- A and B **do not regain raising rights** from this short raise

### Example B — All-In Meets Min Raise and DOES Reopen Betting

- BB = 20, last_raise_increment = 20
- Player all-in increases table bet from 20 to 40 (last_raise_increment = 20)

Result:

- Table bet becomes 40
- `last_raise_increment` updates to 20
- Other ACTIVE players’ `acted_this_street` reset to False (reopen)
- They may now call, fold, or raise again (subject to stack)
