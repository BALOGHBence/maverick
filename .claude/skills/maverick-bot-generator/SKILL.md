---
name: maverick-bot-generator
description: Scaffold a new Maverick Player subclass with a named strategy. Auto-invoked when the user wants to create a poker bot, implement a player strategy, or write a decide_action method for Maverick.
allowed-tools: Read, Glob
---

You are helping the user create a new Maverick poker bot by scaffolding a `Player` subclass.

## Step 1 – Gather requirements

If the user has not already specified the following, ask for them (all at once, in a single message):

1. **Class name** — e.g. `BluffingBot`, `NitBot`
2. **Strategy style** — e.g. tight/loose, aggressive/passive, GTO-inspired, bluff-heavy, calling station, etc.
3. **Use hand strength estimation?** — `estimate_holding_strength` runs a Monte Carlo simulation and is accurate but slow; confirm whether to include it
4. **Output file path** — where to write the new file (e.g. `src/maverick/players/my_bot.py`)
5. **Include `on_event` hook?** — optional, for reacting to game events

## Step 2 – Read existing archetypes for patterns

Read one or two similar archetype files from `src/maverick/players/archetypes/` to ground the implementation in established patterns:

- Tight/aggressive → `tight_agressive.py`
- Loose/passive → `loose_passive.py`
- Bluff-heavy → `maniac.py`
- GTO-inspired → `gto.py`
- Calling station → `hero_caller.py`

## Step 3 – Scaffold the player

Generate the complete file. Requirements:

- Subclass `Player` from `maverick.player`
- Import `ActionType` from `maverick.enums` and `PlayerAction` from `maverick.playeraction`
- Use `TYPE_CHECKING` guard for the `Game` type hint (avoids circular imports)
- Include a `cls_uid` class attribute — generate a fresh UUID4 hex string (32 hex chars, no dashes)
- Implement `decide_action` with the full signature:
  ```python
  def decide_action(
      self,
      *,
      game: "Game",
      valid_actions: list[ActionType],
      min_raise_amount: int,
      call_amount: int,
      min_bet_amount: int,
  ) -> PlayerAction:
  ```
- Always return a `PlayerAction`; as a last resort fall back to `FOLD`
- **`PlayerAction.amount` is the delta chips to add** — it is NOT the total bet size
- If hand strength is used, call `estimate_holding_strength` from `maverick.utils`
- Add a docstring describing key traits, strengths, and weaknesses (follow the archetype style)
- If `on_event` is requested, add:
  ```python
  def on_event(self, event: "GameEvent", game: "Game") -> None: ...
  ```
  with the import `GameEvent` from `maverick.events`

## Step 4 – Write the file

Write the scaffolded code to the output path the user specified. Then remind the user:

> To use this bot, import it and seat it in a `Table`. Run `uv run pytest` to check for any issues.
