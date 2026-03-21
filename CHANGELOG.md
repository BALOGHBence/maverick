# Changelog

All notable changes to this project will be documented in this file. If you are interested in bug fixes, enhancements etc., best follow the project on GitHub.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `uid` and `ts` fields to the `GameState` class.
- Added `GAME_STATE_CHANGED` event type to `GameEventType`. This event is emitted every time the game state transitions to a new instance and carries a `before`/`after` payload with the full serialized `GameState` before and after the change.
- Added `EventBus.has_subscribers(event_type)` method that returns `True` if at least one handler is subscribed to the given event type.

### Changed

- The `is_betting_round_complete` function of the `GameState` class has been turned into a property.
- `GameState` is now a fully immutable (frozen) Pydantic model. Direct attribute assignment raises a `ValidationError`. All state mutations are performed internally via `model_copy`.

## [0.6.0] - 2026.03.20

### Added

- The `PlayerAction` class has a new `payload` field that allows passing an arbitrary dictionary associated with the decision of a player.
- The `PlayerAction` class has a new `decision_time_seconds` field that records how long (in seconds) the player took to make their decision. The game engine sets this automatically; it defaults to `None`.

### Changed

- Harmonized player identifier naming convention: `Player.id` → `Player.uid`, `PlayerAction.player_id` → `PlayerAction.player_uid`, `GameEvent.player_id` → `GameEvent.player_uid`, and `PlayerLike.id` → `PlayerLike.uid`. All internal usages in `game.py`, `table.py`, and all built-in player classes have been updated to the canonical `uid`/`player_uid` names.

### Deprecated

- `Player.id` instance attribute is deprecated; use `Player.uid` instead. The `id` property still works but emits a `DeprecationWarning`.
- `Player.__init__(id=...)` parameter is deprecated; use `uid=` instead. Passing `id=` still works but emits a `DeprecationWarning`.
- `PlayerAction.player_id` field is deprecated; use `player_uid` instead. Constructing with `player_id=` and accessing `.player_id` still work but emit a `DeprecationWarning`.
- `GameEvent.player_id` field is deprecated; use `player_uid` instead. Constructing with `player_id=` and accessing `.player_id` still work but emit a `DeprecationWarning`.
- `PlayerLike.id` protocol attribute is deprecated; use `uid` instead.

## [0.5.1] - 2026.03.18

### Added

- Added a `game_uid` read-only property to the `Game` class that exposes a unique identifier (32-character hex UUID) for each game session. A new `game_uid` is generated every time the `GAME_STARTED` event is processed, so reusing a `Game` instance across multiple sessions always produces a fresh identifier. The value is `None` before `start()` is called.

## [0.4.0] - 2026.02.22

### Added

- Added `cls_uid` class attribute to all player classes for unique identification and runtime lookup via `Player.get_by_uid()`.

## [0.3.0] - 2026.02.14

- Added new positional properties to `Game`: `button`, `small_blind`, and `big_blind`.
- Extended `GameState` with `small_blind_position` and `big_blind_position` fields.

## [0.2.3] - 2026.02.07

- Added `ELIMINATED` state to `PlayerStateType` enum for better player state tracking.

## [0.2.1] - 2026.01.25

### Fixed

- Handled edge case in game flow logic, where all players go either all-in or fold pre-flop.

## [0.2.0] - 2026.01.25

### Deprecated

- The `GameStateType` enum is deprecated, use `GameStage` instead. Also, the `state_type` field of `GameState` is also depracated. Use `GameState.stage` instead.

### Removed

- `SHOWDOWN` was removed from the streets in the `Street` enum.

### Added

- New event types added to the `GameEventType` class:
  - `SHOWDOWN_STARTED`
  - `BETTING_ROUND_STARTED`
  - `POT_WON`
  - `PLAYER_CARDS_REVEALED`
  - `PLAYER_ELIMINATED`

- New code was added to the `Game` class to emit the newly introduced events.

- `Table` class to manage seats and table related state.

- The `GameEvent` class has a new field called `stage`.

### Fixed

- Showdown logic was corrected, now it builds side pots correctly.

## [0.1.0] - 2026.01.22

This is the first release.
