# Maverick NLHE Betting Rules — Implemented Semantics & Edge Cases

This document summarizes the **Texas Hold’em No‑Limit (NLHE)** rules that came up in our discussion, and—most importantly—**the exact semantics implemented by this engine** where different poker engines sometimes diverge.

The goal is that **users of the library can predict behavior precisely**, especially around **minimum raises** and **all‑in edge cases**.

---

## Glossary

- **Street**: PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN
- **Button (BTN)**: Dealer position that rotates each hand.
- **Small Blind (SB)** and **Big Blind (BB)**: forced bets posted pre-flop.
- **Current bet (table bet)**: the amount players must match on the current street.
- **Player current bet**: how much a player has put in on the current street toward matching the table bet.
- **All-in**: player has committed all chips; they cannot take further actions.
- **Minimum raise size** (aka *min raise increment*): the minimum amount by which the table bet must increase for a raise to be “full”.

---

## 1) Blind posting & first-to-act order

### Multi-way (3+ players)
- **SB** is the player **immediately left of the button**.
- **BB** is the player **immediately left of the SB**.
- **First to act pre-flop** is the player **left of the BB** (*UTG*).

### Heads-up (2 players) — special rules (IMPORTANT)
In heads-up NLHE, rules differ from multi-way:

- **Button posts the Small Blind**
- The other player posts the Big Blind
- **Button acts first pre-flop**
- **Big blind acts first on all post-flop streets**

✅ **This engine implements the real heads-up rules above.**  
⚠️ Many homegrown engines accidentally treat heads-up like 3+ players; this library **does not**.

---

## 2) Action semantics: BET vs RAISE vs CALL vs CHECK

### CHECK
- Allowed only if the player has already matched the current table bet:
  - `player.current_bet == table.current_bet`

### CALL
- Puts in exactly enough chips to match the current table bet *if possible*.
- If the player doesn’t have enough chips, they put in **their remaining stack** and become **ALL_IN**.

### BET (opening bet)
- Only allowed when there is no bet yet on this street:
  - `table.current_bet == 0`
- Must be at least `min_bet` (engine-defined, typically BB on post-flop in this codebase).
- A BET sets both:
  - `table.current_bet = bet_amount`
  - `last_raise_size = bet_amount` (first bet sets the min raise increment for the next raise)

### RAISE (raise-by semantics)
**This is a major implementation choice:**

- In this engine, `RAISE.amount` is **raise-by** / **chips-to-add** from stack,
  not “raise-to”.
- That means `RAISE.amount` is the number of chips the player adds **on top of their current street contribution**.

Example (pre-flop, BB=20):
- Player has contributed 0 so far and faces `table.current_bet = 20`.
- `RAISE.amount = 40` means:
  - player adds 40 chips total
  - first 20 chips are the call portion
  - remaining 20 chips increase the table bet
  - resulting table bet becomes 40
  - raise size (increment) is 20

⚠️ Many poker UIs speak “raise **to** X”, while internal engines often store “raise **by** Y”.  
This library explicitly uses **raise-by** for `PlayerAction.amount`.

---

## 3) Minimum raise rule (No-Limit Hold’em)

### Concept
A **full raise** must increase the table bet by at least the **previous raise size**.

- Let `old_table_bet` be the current table bet before the action.
- Let `new_table_bet` be the table bet after the action.
- Let `raise_size = new_table_bet - old_table_bet`.
- Let `last_raise_size` track the last **full** bet/raise increment.

Rule:
- A non-all-in **RAISE** is valid only if:
  - `raise_size >= last_raise_size`

### Engine behavior
- **BET** sets `last_raise_size = bet_amount` (first bet defines the min raise increment).
- A **full raise** updates `last_raise_size` to the new `raise_size`.
- A **short all-in that does not meet the minimum** does **not** update `last_raise_size`.

---

## 4) All-in edge cases: “short all-in” and whether it reopens betting

This is the most important edge case from the discussion.

### Short all-in raise
A player goes all-in and the table bet increases, but by **less than** the minimum raise increment.

Example:
- `old_table_bet = 20`
- `last_raise_size = 20`
- player can only increase table bet to 30
- so `raise_size = 10 < 20`

### Does it reopen betting?
Poker rule of thumb:
- **No**, it does **not** reopen betting for players who already acted.
- Players who have already acted and are not facing a new full raise typically **do not** regain the right to raise.

✅ **This engine implements:**
- Betting is reopened **only** if `raise_size >= last_raise_size`.

Implications:
- If a short all-in happens, **players who already acted are NOT reset** to `acted_this_street = False`.
- But if they are now **facing a call** (because `table.current_bet` increased above their `current_bet`), they may still need to act again (see next section).

---

## 5) Acting flags vs “still facing a bet” (key implementation nuance)

The engine tracks:
- `player.acted_this_street` — whether the player has acted since the last “reopen”.
- `player.current_bet` — their contribution this street.
- `table.current_bet` — the amount required to match.

### Important nuance
A player may have `acted_this_street == True` and still be required to act again if:

- `player.current_bet < table.current_bet`

This happens in the “short all-in increases the bet” scenario:
- players who already acted may still need to **CALL** the extra amount (or fold).
- **but they are not “reset”** to regain raising rights unless the raise was full.

✅ Implementation consequence:
- Turn selection considers a player eligible if:
  - they have not acted this street **OR**
  - they are currently facing a call (their bet is below the table bet).

This is what makes “short all-in does not reopen betting” compatible with correct calling behavior.

---

## 6) Betting round completion (especially with all-ins)

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

---

## 7) What this engine does NOT cover (yet)

Depending on your roadmap, clarify these if/when implemented:

- **Side pot construction** and distributing multiple side pots at showdown.
- **Bet sizing rules** beyond minimums (e.g., post-flop min bet conventions).
- **Re-raise rights** nuances for multi-way short all-ins and “cap” behavior.
- **Straddle** and other forced bets.
- **Dead blinds** when players enter/leave between hands.
- **Posting order adjustments** when seats are missing (e.g., button skipping empty seats).

If any of these exist in the codebase later, update this document to match.

---

## 8) Practical examples (quick reference)

### Example A — short all-in does NOT reopen betting
- BB = 20, last_raise_size = 20
- Players A and B acted already and matched 20
- Player C goes all-in and increases table bet to 30 (raise_size = 10)

Result:
- Table bet becomes 30
- `last_raise_size` stays 20
- A and B **must act again** only to call the extra 10 (or fold)
- A and B **do not regain raising rights** from this short raise

### Example B — all-in meets min raise and DOES reopen betting
- BB = 20, last_raise_size = 20
- Player all-in increases table bet from 20 to 40 (raise_size = 20)

Result:
- Table bet becomes 40
- `last_raise_size` updates to 20
- Other ACTIVE players’ `acted_this_street` reset to False (reopen)
- They may now call, fold, or raise again (subject to stack)

---

## 9) Summary of “engine-to-engine difference” decisions

These are the key choices you should surface in docs/API:

1. **Heads-up blinds**: Button posts SB (implemented).
2. **Raise amount semantics**: `RAISE.amount` is **raise-by** (implemented).
3. **Minimum raise enforcement**: based on **raise size increment** (implemented).
4. **Short all-in**: does **not** reopen betting unless it meets minimum raise (implemented).
5. **Action eligibility**: a player can be required to act again even if they “already acted” if they’re still facing a call (implemented).

---

## Contact / versioning

If you change any of the rules above, bump the library version and update this file,
because bots and users may rely on these exact semantics.
