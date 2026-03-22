# Changelog

All notable changes to this project will be documented in this file. If you are interested in bug fixes, enhancements etc., best follow the project on GitHub.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `uid` and `ts` fields to the `GameState` class.
- Added `GAME_STATE_CHANGED` event type to `GameEventType`. This event is emitted every time the game state transitions to a new instance and carries a `before`/`after` payload with the full serialized `GameState` before and after the change.
- Added `EventBus.has_subscribers(event_type)` method that returns `True` if at least one handler is subscribed to the given event type.
- Added `all_stacks_at_game_start` property to the `Game` class.
- Added `PlayerSnapshot` frozen Pydantic model (fields: `uid`, `name`, `state`) that captures observable player data at a point in time, decoupled from strategy logic.
- Added `Game.get_player_snapshot(uid)` helper method that returns the current `PlayerSnapshot` for a player by UID or player object.

### Changed

- Eliminated players are now **retained** in `game.state.players` with `state_type=PlayerStateType.ELIMINATED` for the full game duration. Previously, players whose stack reached zero were immediately removed from `game.state.players` after each hand. Code that needs only active or eligible players should use `game.state.get_active_players()` or `game.state.get_players_in_hand()`.
- **Breaking (minor):** `PLAYER_LEFT` is no longer emitted when a player is eliminated. Elimination is exclusively signalled by the `PLAYER_ELIMINATED` event. Code that listened to `PLAYER_LEFT` to detect eliminations should switch to `PLAYER_ELIMINATED`.
- **Breaking:** `GameState.community_cards` type changed from `list[Card]` to `tuple[Card, ...]`. This makes the immutability intent explicit and prevents in-place mutation at the type level. Code that relies on `community_cards` being a `list` (e.g. calling `.append()` or `.extend()` on it) must be updated.
- `GAME_STATE_CHANGED` is now emitted when community cards are dealt (flop, turn, and river). Previously, the deal methods mutated the card list in-place, bypassing `_update_state` and suppressing the event.
- The `is_betting_round_complete` function of the `GameState` class has been turned into a property.
- `GameState` is now a fully immutable (frozen) Pydantic model. Direct attribute assignment raises a `ValidationError`. All state mutations are performed internally via `model_copy`.
- `PlayerState` is now a fully immutable (frozen) Pydantic model. Direct attribute assignment raises a `ValidationError`. All player-level mutations in the game engine now go through `Game._update_player_state`, which replaces the `PlayerState` via `model_copy` and propagates the change by calling `_update_state`. This ensures `GAME_STATE_CHANGED` is emitted after every logical player state change (fold, all-in transition, stack deduction, stack gain, etc.).
- **Breaking:** `GameState.players` type changed from `list[PlayerLike]` to `list[PlayerSnapshot]`. Each element now contains only observable data (`uid`, `name`, `state`); live strategy objects are no longer stored inside `GameState`. Code that accesses `game.state.players[i].decide_action(...)` or player-specific attributes (e.g. custom `event_counter`) must be updated to obtain the strategy object via `game._strategies[uid]` or subscribe to game events.
- **Breaking:** `Table._seats` now stores player UIDs (`str`) instead of live player objects. `table[seat]` returns a `str` UID or `None`. `Table.seat_player` and `Table.remove_player` no longer mutate `player.state`; seat information is managed exclusively through `PlayerSnapshot` in `GameState`.
- **Breaking:** `Table.next_occupied_seat(active=True)` replaced by `Table.next_occupied_seat(active_uids=...)`. Callers must explicitly pass the set of active player UIDs obtained from `{s.uid for s in game.state.get_active_players()}`.
- **Breaking:** `Player` is now a pure strategy object. The `state` constructor parameter and `state` instance attribute have been removed. All player state lives exclusively in `GameState.players` as `PlayerSnapshot` entries. Code that previously passed `state=PlayerState(stack=...)` to a player constructor must instead pass it to `Game.add_player(player, state=PlayerState(stack=...))`. Code that previously read `player.state.stack` must use `game.get_player_snapshot(player).state.stack` or iterate `game.state.players`.
- **Breaking:** `Game.add_player()` now accepts an optional keyword-only `state` parameter (`PlayerState | dict | None`) that sets the player's initial state. The initial stack/seat previously carried on the player object must now be supplied here.
- **Breaking:** `PlayerLike` protocol no longer includes a `state` attribute.
- **Breaking:** `Player.to_dict()` no longer includes a `"state"` key in the returned dictionary.
- `Game._update_player_state` no longer synchronises the strategy object's `state` attribute. State is now the exclusive responsibility of `GameState`.
- `Game.get_player_snapshot()` now accepts either a UID string or a `PlayerLike` object (in addition to the previous UID-only form).
- `Game._strategies` dict holds all live strategy objects keyed by player UID; `Game.add_player` populates it, `Game.remove_player` clears the entry.
- All built-in player strategies (`FoldBot`, `CallBot`, `AggressiveBot`, and all archetype bots) updated to retrieve their current state via `game.get_player_snapshot(self.uid)` instead of `self.state`.
- `GameState.get_active_players()` and `GameState.get_players_in_hand()` now return `list[PlayerSnapshot]`.
- **Breaking:** `deck` has been removed from `GameState`. The active deck is now held by `Game._deck` and exposed via the read-only `game.deck` property. Code that previously accessed `game.state.deck` must be updated to use `game.deck`.

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
