# Overview

Maverick is a Python library for simulating poker games with a small, composable API.
It’s designed for experiments: swapping player strategies, observing events, and running repeatable simulations.

## What You Can Do With Maverick

- Run a full game loop with betting rounds, dealing, and showdown.
- Plug in custom players (bots/agents) by implementing a single `decide_action` method.
- Observe the game through an event stream for logging, analytics, or debugging.
- Evaluate hands and estimate holding strength.

## Core Concepts

### `Game`

{class}`~maverick.game.Game` is the main engine.
It holds the state machine, applies rules, requests actions from players, registers actions, and emits events.

Key inputs:

- Stakes: small blind, big blind (and optional ante)
- Table sizing rules: min/max players
- `max_hands`: stop condition

### `Player` and `PlayerLike`

Players are asked to act when it is their turn. Built-in players live under {mod}`maverick.players`.
For your own strategy, implement the {class}`~maverick.player.Player` abstract base class (or any object that satisfies {class}`~maverick.protocol.PlayerLike`).

The required method is keyword-only:

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
    ...
```

Where:

- `valid_actions` tells you what is legal right now.
- `call_amount` is how many chips you must add *now* to call.
- `min_raise_amount` is the minimum extra chips you must add *now* to complete a minimum raise.
- `min_bet_amount` is the minimum chips you must add *now* to make a bet.

### `PlayerAction` and `ActionType`

Players return a {class}`~maverick.playeraction.PlayerAction` that contains an {class}`~maverick.enums.ActionType` (e.g. {data}`~maverick.enums.ActionType.FOLD`, {data}`~maverick.enums.ActionType.CHECK`, {data}`~maverick.enums.ActionType.CALL`, {data}`~maverick.enums.ActionType.BET`, {data}`~maverick.enums.ActionType.RAISE`, {data}`~maverick.enums.ActionType.ALL_IN`) and an optional {attr}`~maverick.playeraction.PlayerAction.amount`.
The engine validates actions against the current rules and state.

### Rules and State

- {class}`~maverick.rules.PokerRules` groups dealing/stakes/showdown rule sets.
- {class}`~maverick.state.GameState` and {class}`~maverick.playerstate.PlayerState` hold the runtime state.

If you’re building simulations, you typically configure rules once and then run many games.

### Events

The engine emits {class}`~maverick.events.GameEvent` instances (via an internal {class}`~maverick.eventbus.EventBus`) as the game progresses.
This is the primary integration point for:

- logging
- metrics
- hand replays
- custom tooling

See {doc}`user_guide/events` for details.

## A Minimal Flow

For a runnable end-to-end example, see {doc}`getting_started`.
At a high level:

1. Create a {class}`~maverick.game.Game`
2. Add players via {meth}`~maverick.game.Game.add_player`
3. Call {meth}`~maverick.game.Game.start`

## Where To Go Next

- {doc}`getting_started`
- {doc}`user_guide/index`
- {doc}`api_reference`
