# Pull Request Summary: Synchronous Event System

## Overview

This PR implements a minimal, synchronous, deterministic event system that allows external observers (and players) to react to game events **without affecting engine control flow or state**.

## Changes Made

### 1. New File: `src/maverick/events.py`
- Introduced immutable `GameEvent` payload model
- Uses Pydantic with `frozen=True` for immutability
- Contains snapshot of game state at event time
- Properties: `type`, `hand_number`, `street`, `player_id`, `action`, `amount`, `pot`, `current_bet`

### 2. Updated: `src/maverick/game.py`
- Added `_listeners` dictionary to store event handlers
- Implemented `on(event_type, handler)` method for registering handlers
- Implemented `_emit(event)` method for synchronous event dispatch
- Implemented `_create_event()` helper for creating event payloads
- Added event emissions at all required transition points:
  - GAME_STARTED
  - HAND_STARTED
  - POST_BLINDS
  - PLAYER_ACTION (after each action)
  - BETTING_ROUND_COMPLETED
  - DEAL_FLOP
  - DEAL_TURN
  - DEAL_RIVER
  - SHOWDOWN
  - HAND_ENDED
  - PLAYER_JOINED
  - PLAYER_LEFT
- Exception handling: All handler exceptions are caught, logged, and swallowed

### 3. Updated: `src/maverick/player.py`
- Added optional `on_event(event)` hook to Player class
- Default implementation does nothing (pass)
- Subclasses can override to observe events
- Exceptions in player hooks are caught and logged

### 4. Updated: `src/maverick/__init__.py`
- Exported `GameEvent` class

### 5. New File: `tests/test_event_system.py`
- Comprehensive test suite with 16 tests
- Tests cover:
  - GameEvent model immutability and validation
  - Event subscription and handler registration
  - Event emission at transition points
  - Handler execution order (registration order)
  - Exception safety (handlers don't crash engine)
  - No-op behavior when no handlers registered
  - Player-level event hooks
  - Event payload accuracy

### 6. New Files: Examples and Documentation
- `examples/demo_event_system.py` - Working demo showing event system in action
- `examples/README.md` - Documentation with usage examples

## Design Principles Followed

✅ **Fully synchronous** - No async/await, no threads  
✅ **Deterministic execution** - Handlers called in registration order  
✅ **Engine-owned lifecycle** - Events emitted after state mutations  
✅ **Observer-only** - No state mutation allowed in handlers  
✅ **Exception-safe** - Handler exceptions caught and logged  
✅ **Backward compatible** - No behavior change when no handlers registered  

## Testing

All 125 tests pass, including:
- 109 existing tests (unchanged behavior verified)
- 16 new event system tests

## Example Usage

```python
from maverick import Game, GameEvent, GameEventType

game = Game()

# Register global event handler
def log_actions(event: GameEvent):
    if event.type == GameEventType.PLAYER_ACTION:
        print(f"Player {event.player_id} took action: {event.action.name}")

game.on(GameEventType.PLAYER_ACTION, log_actions)

# Player-level event hook
class ObservantPlayer(Player):
    def on_event(self, event: GameEvent):
        print(f"I observed: {event.type.name}")

# Add players and start game
game.add_player(ObservantPlayer(id="p1", name="Player1", state=PlayerState(stack=1000)))
game.start()
```

## Non-Goals (Intentionally NOT Implemented)

❌ Async event handlers  
❌ Ability for handlers to block or cancel actions  
❌ State mutation inside handlers  
❌ Event filtering or routing logic  
❌ Event priorities  
❌ Replay or persistence (future enhancement)  

## Files Changed

- `src/maverick/events.py` (new)
- `src/maverick/game.py` (modified)
- `src/maverick/player.py` (modified)
- `src/maverick/__init__.py` (modified)
- `tests/test_event_system.py` (new)
- `examples/demo_event_system.py` (new)
- `examples/README.md` (new)

## Testing Instructions

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# Run event system tests only
python -m unittest tests.test_event_system -v

# Run demo
python examples/demo_event_system.py
```

## Breaking Changes

None. This is a purely additive change. When no event handlers are registered, the engine behaves exactly as before.

## Future Enhancements (Not in this PR)

- Event replay/persistence
- Event filtering DSL
- More granular events (e.g., BLINDS_POSTED_SMALL, BLINDS_POSTED_BIG)
- Event middleware/pipelines
