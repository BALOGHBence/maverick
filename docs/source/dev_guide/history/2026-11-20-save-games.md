---
myst:
  html_meta:
    description: "Games can be saved to disk as versioned JSON, replayed step by step without the players, and resumed from the last completed hand, also after a crash."
---

# Saving, replaying and resuming games

| | |
|---|---|
| **Date** | 2026-11-20 |
| **PR / Issues** | #111, closes #103 |
| **Version** | 0.7.0 (unreleased) |
| **Breaking** | No |

## Summary

Games can now be saved to disk with `Game(save_dir=...)`. A save is a directory with a
header, an append-only event log with the full table state after every event, and a
checkpoint written whenever a hand ends. `Replay` steps through the log without creating
a game or any players. `Game.load(save_dir, players=...)` restores the engine from the
checkpoint, including its random number generator and each player's exported state, and
`start()` continues from the end of the last completed hand, also after the process was
killed. A resumed game deals the same cards as one that was never interrupted, in both
isolation modes. Saves are versioned JSON only: loading never unpickles anything or
imports code named in the files.

## Details

### Motivation

Issue #103 asked for replays of finished or interrupted games, and for resuming long
games and tournaments after a crash. Both prerequisites were settled in #109: the engine
owns its random number generator, and `export_state`/`import_state` restore a player in
both isolation modes.

### Changes

- **`maverick.savegame`** (new module): the file format as Pydantic models
  (`SaveHeader`, `Checkpoint`, `EventRecord`, ...), `SAVE_FORMAT_VERSION`,
  `SaveFormatError`, readers that check the version before validating, and
  `SaveWriter`, which buffers the events of a hand and writes them together with the
  checkpoint. Files are written with owner-only permissions; the checkpoint is replaced
  atomically.
- **`maverick.replay.Replay`** (new): loads a save and moves a cursor with `forward`,
  `backward`, `seek` and `go_to_hand`; `hand(n)` and iteration return
  `(event, state)` pairs. States are validated when first used.
- **`Game`**:
  - New `save_dir` argument and property. A directory that already holds a save is
    rejected, so a save is never overwritten.
  - Events other than `GAME_STATE_CHANGED` are recorded with the state after them.
  - The hand boundary logic moved from the `HAND_ENDED` branch into
    `_eliminate_busted_players()` and `_continue_between_hands()`. The latter also
    starts the first hand after `GAME_STARTED`, and continues a loaded game.
  - A checkpoint is written after `GAME_STARTED` and after every `HAND_ENDED` (after
    eliminations). The log is flushed when the game ends.
  - New `Game.load()` classmethod. It validates the save, checks that the supplied
    players match the seated ones, restores the table, state, history, random state,
    revealed holdings and counters, starts workers in process mode, imports each
    player's state, and cuts the log back to the checkpoint.
  - `start()` continues a loaded game after emitting `GAME_RESUMED`.
- **`GameEventType.GAME_RESUMED`**, added at the end of the enumeration.
- **`DealingRules`** accepts the string keys JSON makes of `board_deal_pattern`, so
  `PokerRules` survives a round trip through JSON.
- **Docs:** new user-guide page `saving_games.md`, a note in `player_isolation.md`, a
  new section in {doc}`../design_decisions`, and the API reference.

### Breaking changes and migration

None. Games without `save_dir` behave as before.

### Design decisions and alternatives considered

The design is described in {doc}`../design_decisions`, section "Games are saved as
JSON, between hands". Choices made for the open questions of #103:

- **Failed exports:** the checkpoint records the failure and the game continues; on
  load the player continues without its state, with a warning. Failing the checkpoint
  loudly would let one bot stop a tournament.
- **Resume marker:** a `GAME_RESUMED` event was added.
- **States or events for replay:** a state per event. Simple, about 125 KB per hand with
  six players. A compact format can come later (see follow-ups).
- **Seeds for bot randomness in workers:** not part of this change; tracked in #108.
- **Format:** a directory, not a single file, so the log can be appended to and the
  checkpoint replaced atomically. No compression.
- **`players` is a list, not a `{uid: player}` mapping** as sketched in the issue: the
  players carry their UIDs, so a mapping would only add a way to disagree.
- **Isolated bots reading saves** (the comment on #103): files are created with mode
  `0o600`, and a hand's events are only written once it is over, so a running hand's hole
  cards are never on disk. The checkpoint's random state still predicts the next hand,
  and workers run as the engine's user. Leaving the random state out would break exact
  resumes, so this is documented instead: keep saves out of the workers' reach (#107).

### Performance

100 hands with six cheap bots (five `CallBot`, one `AggressiveBot`), median of 5 runs:
0.65s without saving, 1.0s with saving, and a 12.5 MB log. Games without `save_dir` only
pay a `None` check per event.

### Testing

New `tests/test_savegame.py`:

- 10 hands deal the same cards and end in the same state as 5 hands, load and 5 more,
  with a bot whose decisions depend on its exported state, in both isolation modes. The
  replays have the same events, plus `GAME_RESUMED`.
- A subprocess that is killed with `os._exit` in hand 4 resumes from the end of hand 3
  and ends like an uninterrupted game. Resuming before the first hand ended works too.
- Events after the checkpoint, including a line cut off by a crash, are dropped on load.
- Replays create no players, match the game's history and final state, show every
  holding, and the cursor methods behave at the edges.
- Saves contain JSON only; loading with `pickle.load(s)` and
  `importlib.import_module` patched to fail works; extra fields such as a class path
  are rejected; unsupported header and checkpoint versions fail with a message that
  names the version; malformed and inconsistent files raise `SaveFormatError`.
- Supplied players must match the table; eliminated players can be left out; failed
  imports raise; failed exports are recorded and restored fresh, in both modes.
- Saves are not overwritten, and their files are private on POSIX.

### Follow-ups and known limitations

- Saves happen between hands only. Mid-hand saves would also need the deck and the
  betting state.
- The log is large. A compact format (actions only, with an engine mode that replays
  them) or compression can be added with a new format version.
- `Replay` has no built-in spectator view; `redact_state` produces one.
- Isolated bots can read saves of the game they play in, unless the game runs in a
  container or as a separate user (#107).
