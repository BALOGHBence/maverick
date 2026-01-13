# Event System Example

This example demonstrates the synchronous event dispatch system in Maverick.

## Usage

```bash
python examples/demo_event_system.py
```

## Features Demonstrated

1. **Global Event Handlers**: Register handlers for specific event types
2. **Multiple Handlers**: Multiple handlers can listen to the same event
3. **Player-Level Hooks**: Players can implement `on_event()` to observe events
4. **Event Payload**: Access game state snapshot through immutable `GameEvent` objects
5. **Exception Safety**: Handlers that raise exceptions don't crash the game

## Key Concepts

### Registering Event Handlers

```python
from maverick import Game, GameEvent, GameEventType

game = Game()

def my_handler(event: GameEvent):
    print(f"Event: {event.type.name}, Pot: {event.pot}")

game.on(GameEventType.PLAYER_ACTION, my_handler)
```

### Player-Level Event Hooks

```python
from maverick import Player, GameEvent

class ObservantPlayer(Player):
    def on_event(self, event: GameEvent):
        # React to any game event
        print(f"I saw: {event.type.name}")
```

### Available Events

- `GAME_STARTED` - Game begins
- `HAND_STARTED` - New hand starts
- `POST_BLINDS` - Blinds have been posted
- `PLAYER_ACTION` - Player takes an action
- `BETTING_ROUND_COMPLETED` - Betting round completes
- `DEAL_FLOP` - Flop cards dealt
- `DEAL_TURN` - Turn card dealt
- `DEAL_RIVER` - River card dealt
- `SHOWDOWN` - Showdown occurs
- `HAND_ENDED` - Hand ends
- `PLAYER_JOINED` - Player joins the table
- `PLAYER_LEFT` - Player leaves the table

## Event Payload

Each `GameEvent` contains:

- `type`: The event type
- `hand_number`: Current hand number
- `street`: Current betting street
- `pot`: Current pot size
- `current_bet`: Current bet amount
- `player_id`: Player involved (if applicable)
- `action`: Action taken (for PLAYER_ACTION events)
- `amount`: Amount involved (if applicable)

All events are immutable and safe to log, store, or replay.
