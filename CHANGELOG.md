# Changelog

All notable changes to this project will be documented in this file. If you are interested in bug fixes, enhancements etc., best follow the project on GitHub.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
