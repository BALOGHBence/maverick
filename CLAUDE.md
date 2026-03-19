# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Maverick** is a Python library for simulating various poker games with custom player strategies. It provides a composable, event-driven API for building and testing poker bots.

- **Package manager:** `uv`
- **Python:** >= 3.12
- **Source layout:** `src/maverick/`

## Commands

```bash
# Install dependencies (dev includes test, docs, formatting)
uv sync --group dev

# Run tests (pytest runs with -q by default via pytest.ini)
uv run pytest

# Run a single test file
uv run pytest tests/test_game.py

# Run a single test by name
uv run pytest tests/test_game.py::test_function_name

# Run tests with coverage
uv run pytest --cov-report=term-missing --cov-config=.coveragerc --cov=maverick

# Format code (Black, line length 88)
uv run black src

# Build the package
uv build
```

## Architecture

### Core Components

**Game state machine** (`game.py`) — The central engine. Drives the full poker hand lifecycle: seating → blinds → betting rounds → showdown → pot distribution. Emits events through the `EventBus` after every significant action.

**Rules system** (`rules.py`) — `PokerRules` is a Pydantic model composed of:
- `DealingRules` — `max_players`, `min_players`, `hole_cards`, `board_cards_total`, `board_deal_pattern` (maps `Street` → int for custom deal sequences)
- `StakesRules` — `small_blind`, `big_blind`, `ante`
- `ShowdownRules` — `hole_cards_required` (how many of a player's own hole cards must be used; 0 for Hold'em, 2 for Omaha)

**Player system** (`player.py`, `protocol.py`) — The abstract `Player` base class uses `PlayerMeta` metaclass for auto-registration into `_registered_players`. All subclasses get a `cls_uid` class attribute for runtime lookup via `Player.get_by_uid()`. The `PlayerLike` protocol enables duck-typed player implementations without subclassing.

**Player interface** — Every player must implement:
```python
def decide_action(
    self,
    *,
    game: "Game",
    valid_actions: list[ActionType],
    min_raise_amount: int,
    call_amount: int,
    min_bet_amount: int,
) -> PlayerAction: ...
```
Optional hook: `on_event(event: GameEvent, game: Game)` — called for every game event if defined.

**State models** (`state.py`, `playerstate.py`) — `GameState` and `PlayerState` are immutable frozen Pydantic models. `GameState` captures the full table snapshot (street, pot, community cards, positions, all player states).

**Event system** (`events.py`, `eventbus.py`) — `GameEvent` is an immutable frozen Pydantic model with `extra="forbid"`. Register handlers via:
```python
token = game.event_bus.subscribe(
    event_type,       # GameEventType or None for all
    handler,          # callable(GameEvent, Game)
    priority=0,       # higher priority executes first
    once=False,       # auto-unsubscribe after first call
    mask=None,        # optional filter function
)
game.event_bus.unsubscribe(token)
```

**Table** (`table.py`) — Manages seating, seat assignment, and button position across hands. `Table.next_occupied_seat(start, active=False)` uses circular modulo navigation.

**Hand evaluation** (`utils/scoring.py`, `utils/holding_strength.py`) — `score_hand(cards)` evaluates a 5–7 card hand into `(HandType, float_score)`. `estimate_holding_strength(holding, community_cards, deck)` runs a Monte Carlo simulation for decision-making.

### Non-Obvious Semantics

- **`PlayerAction.amount`** is the delta chips from the player's stack to put into the pot — it is **not** the total bet after the action. This is a common source of confusion.
- **`HandType`** is a comparable enum (`<`, `<=`, `>`, `>=` all supported).
- **Game constructor parameters** override corresponding `PokerRules` fields if provided, enabling quick configuration without building a full rules object.
- **`GameState` serialization** stores player class names for later reconstruction. Custom `field_serializer` handles this.
- Event handlers can safely subscribe/unsubscribe during event processing without affecting the current dispatch cycle.

### Data Flow

```
Game.start()
  → deal hole cards
  → post blinds
  → for each betting round:
      → call player.decide_action() for each active player
      → validate action → update pot/state → emit event
  → deal community cards (flop/turn/river)
  → showdown: score hands → distribute pot → emit POT_WON events
  → next hand or FINISHED
```

### Enums (`enums.py`)

Key enums used throughout: `Street`, `GameStage`, `ActionType`, `GameEventType`, `HandType`, `PlayerStateType` (ACTIVE, FOLDED, ALL_IN, ELIMINATED).

### Built-in Players (`players/`)

- **Simple:** `FoldBot`, `CallBot`, `AggressiveBot`
- **Archetypes:** 15 strategy bots (TightAggressive, LoosePassive, GTO, Shark, Fish, etc.) in `players/archetypes/`

## Git Workflow

- **Branches:** `main` (stable) and `dev` (development). Feature branches cut from `dev`, PRs target `dev`. Feature branches follow the naming convention `feature/<the name of the feature branch>`
- **PRs to `main`** only come from `dev` (enforced by CI).
- **Versioning:** Semantic versioning; `CHANGELOG.md` follows Keep a Changelog format.

## Testing

- Tests live in `tests/`, configured in `pytest.ini` and `.coveragerc`.
- Branch coverage is enabled. CI uploads results to Codecov.
- CI runs on PRs to `dev` or `main` via `.github/workflows/testing_and_coverage.yml`.
