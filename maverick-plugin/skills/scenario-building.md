---
name: maverick-scenario-builder
description: Build a reproducible Maverick game scenario for testing or demonstration. Auto-invoked when the user wants to set up a game, create a test hand, construct a scenario, or reproduce a specific poker situation.
allowed-tools: Read, Glob
---

You are helping the user construct a reproducible Maverick game scenario.

## Step 1 – Gather requirements

If the user has not already specified the following, ask for them (all at once, in a single message):

1. **Game variant** — Texas Hold'em (default) or Omaha
2. **Number of players** — 2 to 9
3. **Stack sizes** — uniform (e.g. 1000 chips each) or custom per player
4. **Stakes** — small blind / big blind (e.g. 5/10)
5. **Purpose** — testing a specific street (pre-flop, flop, turn, river), reproducing a bug, demonstrating a concept, or running a full hand
6. **Player types** — which bots to seat (e.g. `CallBot`, `TightAggressiveBot`, or custom) or placeholders
7. **Event observation needed?** — whether to subscribe to game events for assertions or logging

## Step 2 – Check relevant documentation

Read `docs/build/html/llms.txt` if it exists. Select and read the most relevant pages for the scenario (e.g. user guide pages on `Game`, `Table`, `PokerRules`, event subscription).

If `docs/build/html/llms.txt` does not exist, proceed from built-in knowledge of the Maverick API.

## Step 3 – Generate the scenario

Produce a self-contained Python script or test function. Requirements:

- Import `Game`, `Table` from `maverick`
- Import `PokerRules`, `DealingRules`, `StakesRules`, `ShowdownRules` from `maverick.rules` for non-default variants
- Import player classes from `maverick.players` (or the user's custom module)
- Create a `Table`, seat the players, then create a `Game`
- If events are needed, subscribe before calling `game.start()`:
  ```python
  token = game.event_bus.subscribe(GameEventType.POT_WON, handler)
  ```
- Keep the setup minimal and focused on the scenario's purpose
- Add inline comments explaining non-obvious steps

**Hold'em example skeleton:**
```python
from maverick import Game, Table
from maverick.players import CallBot, TightAggressiveBot

table = Table()
table.seat_player(CallBot(name="Alice"), seat=0)
table.seat_player(TightAggressiveBot(name="Bob"), seat=1)

game = Game(table=table, small_blind=5, big_blind=10, starting_stack=1000)
game.start()
```

**Omaha example skeleton:**
```python
from maverick import Game, Table
from maverick.rules import PokerRules, DealingRules, StakesRules, ShowdownRules
from maverick.enums import Street
from maverick.players import CallBot

rules = PokerRules(
    dealing=DealingRules(hole_cards=4, board_cards_total=5, board_deal_pattern={Street.FLOP: 3, Street.TURN: 1, Street.RIVER: 1}),
    stakes=StakesRules(small_blind=5, big_blind=10),
    showdown=ShowdownRules(hole_cards_required=2),
)

table = Table()
for i, name in enumerate(["Alice", "Bob", "Carol"]):
    table.seat_player(CallBot(name=name), seat=i)

game = Game(table=table, rules=rules, starting_stack=1000)
game.start()
```

## Step 4 – Suggest assertions or next steps

Based on the user's stated purpose, suggest:
- Which `GameEventType` events to subscribe to for the assertion
- How to capture `GameState` snapshots via `game.state`
- How to run the scenario as a pytest test with `assert` statements
