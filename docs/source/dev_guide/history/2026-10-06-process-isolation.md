---
myst:
  html_meta:
    description: "Players can optionally run in separate worker processes, so untrusted bots can't reach the engine through introspection. The mode is set in code, environment variables or pyproject.toml."
---

# Optional process isolation for players

| | |
|---|---|
| **Date** | 2026-10-06 |
| **PR / Issues** | #101, prepares #103 |
| **Version** | 0.7.0 (unreleased) |
| **Breaking** | Minor: seeding `random` after creating a game no longer affects the cards |

## Summary

`PlayerView` closed every API-level leak, but bots still ran in the engine's process, so a
bot written to cheat could reach the `Game` with `sys._getframe` or `gc.get_objects()`.
With `player_isolation="process"`, every player now runs in its own spawned worker
process. The engine sends it pickled views and receives actions as JSON. Players that
time out, raise, return garbage or crash fold instead of stopping the game. The mode and
an optional `decision_timeout` can be set as `Game` arguments, through the
`MAVERICK_PLAYER_ISOLATION` and `MAVERICK_DECISION_TIMEOUT` environment variables, or in
`[tool.maverick]` of `pyproject.toml`, in that order of priority. Bot state crosses the
process boundary through a new pair of optional hooks, `Player.export_state()` and
`Player.import_state()`, called by `Game.get_player_state()` and
`Game.set_player_state()` in either mode. The game now also shuffles and deals with its
own seedable random number generator instead of the global `random` module. In-process
mode stays the default and is as fast as before. Both the state hooks and the generator
are prerequisites for saving and resuming games (#103).

## Details

### Motivation

Results of games with untrusted bots, such as bot tournaments, can't be trusted while
bots share a process with the engine. Python has no access control inside a process, so
this can't be fixed by changing the API. See #101 for the proof of concept.

### Changes

- **`maverick._isolation`** (new private package):
  - `worker.run_worker`: the loop that runs in the worker process. It unpickles the
    player, confirms it is ready, rebuilds the player's `PlayerView` from `ViewDelta`
    messages, calls `decide_action` and the hooks, and answers in JSON.
  - `proxy.ProcessPlayer`: the engine-side `PlayerLike` proxy. It starts the worker,
    forwards decisions and state exports with a sequence number and an optional timeout,
    forwards the hooks the player implements as one-way messages, and raises
    `PlayerFailure` when no valid reply arrives. When it closes the worker, it keeps the
    player's last exported state.
- **`maverick.config`** (new module): `IsolationSettings`, a frozen Pydantic model, and
  `resolve_settings()`, which merges arguments, environment variables and the nearest
  `pyproject.toml` field by field.
- **`PlayerIsolation`** enumeration with `NONE` and `PROCESS`.
- **`Game`**:
  - New `player_isolation` and `decision_timeout` arguments and a `settings` property.
  - In process mode, `add_player` starts a worker before changing any state, so a
    player that can't be isolated is rejected cleanly.
  - `decide_action` and the hooks are called on the proxy if there is one. The public
    members (`button`, `get_current_player()`, ...) still return the original players.
  - A `PlayerFailure` makes the player fold.
  - New `close()` and context manager support. Workers are also stopped when a player
    leaves or is eliminated, and when the game ends.
  - New `get_player_state(player)`. It asks a running worker, falls back to the state
    exported when the worker stopped, or calls the bot directly in-process. The result
    always goes through JSON.
  - New `set_player_state(player, state)`, which restores a state through the worker
    or directly in-process. The state also goes through JSON.
  - New `seed` argument and property. The game creates its own `random.Random` from
    the seed and passes it to every shuffle and deal. Without a seed, one is drawn from
    the global `random` module.
- **`Player.export_state()` / `Player.import_state()`**: a new pair of optional hooks.
  `export_state` returns everything needed to restore the player as a
  JSON-serializable `dict`, and `import_state` restores it. By default they return
  `None` and do nothing.
- **`Deck`**: `build`, `standard_deck`, `shuffle` and `deal` take an optional `rng`.
  They still use the global `random` module by default.
- **Docs:**
  - A new user-guide page, `player_isolation.md`.
  - The `llm_as_player` example now exports its token usage with `export_state`, can
    restore it with `import_state`, and reads it with `get_player_state`, so the cost
    summary works in both isolation modes. Its stored outputs are unchanged, because
    the notebook needs an OpenAI key to run.
  - The reproducibility guide now uses `seed` and was re-executed.

### Breaking changes and migration

In-process mode is the default, and players behave as before. One change in how cards
are dealt:

- The game no longer shuffles and deals with the global `random` module. Seeding
  `random` before creating a game is still reproducible, because the game draws its
  seed from it. Seeding it after the game has been created no longer affects the
  cards. Pass `seed` to `Game` instead.
- For the same seed, the cards differ from those dealt by earlier versions.

### Design decisions and alternatives considered

The current design is described in {doc}`../design_decisions`, section "Players can run
in separate processes". Choices made for the open questions of #101:

- **Process model:** one long-lived worker per player, because bots keep state between
  decisions. A pool would lose that state.
- **Hook overhead:** hooks are sent without waiting for an answer, and only for the
  hooks a player implements, which batches them for free. No per-bot opt-in was needed.
- **`exc_handling_mode`:** unchanged. It still only governs event bus handlers.
  Isolated players always fold on failure, so one bot can't stop a tournament.
- **Resource limits:** left to the user (containers, operating system limits).
- **Reproducibility:** shuffling and `first_button_position` stay in the engine and
  are unaffected. Random numbers in bots are not seeded in workers.
- **`spawn` instead of `fork`:** a forked worker inherits the engine's memory,
  including the `random` state that shuffles the deck.
- **JSON from workers:** the engine never unpickles anything from a worker, because
  that would let a malicious worker run code in the engine. Replies are limited to 1 MB.
- **A pipe per worker instead of `multiprocessing.Queue`:** a queue unpickles whatever
  is taken out of it, so it can't be used for replies from untrusted workers without
  giving up the JSON-only reply path.
- **`export_state`/`import_state` instead of syncing the bot object back:** bot state
  lives in the worker, so data collected on the bot (statistics, LLM token usage, ...)
  was lost to the caller. Sending the bot back pickled would be unsafe for the reason
  above, and mirroring attributes as JSON would fail silently for attributes that can't
  be serialized. An explicit, opt-in `dict` is safe and lets the bot author decide what
  to keep. Listeners need none of this: they run in the engine's process.
- **One pair of hooks for reporting and restoring:** `export_state` was first added for
  reports only. Saving games (#103) needs "everything to restore the player", and two
  pairs of methods with overlapping data would drift apart. The contract was settled
  before 0.7.0 is released, while it can still change without breaking bots.
- **Failed exports return `None`, failed imports raise:** collecting results from many
  bots shouldn't stop because of one, but a state that silently fails to load is worse
  than an error.
- **An engine-owned random number generator:** see {doc}`../design_decisions`, section
  "The game owns its random number generator". In short: in-process players changed
  the cards by using `random`, could predict them with `random.getstate()`, and the
  global state couldn't be saved for #103. The default seed is drawn from `random`, so
  that existing `random.seed(...)` code stays reproducible.
- **Startup handshake:** the worker confirms it could unpickle the player. Without it,
  a player class defined in a notebook would only fail in the worker, and the player
  would silently fold the whole game.
- **Keeping the original players in `_strategies`:** proxies are stored separately, so
  code that compares `game.button` with its own player objects works in both modes.
- **Unknown `[tool.maverick]` keys raise an error,** so a typo such as
  `player_isolaton` doesn't silently leave isolation off.

### Performance

In-process mode, 100 hands with 6 simple bots, median of 5 runs:

| Run | `feature/player-view` | This change |
|---|---|---|
| 1 | 1.78s | 1.98s |
| 2 | 2.01s | 2.01s |

The difference is within run-to-run noise. The fastest runs were 1.70s vs 1.73s and
1.91s vs 1.87s. In-process mode only adds one settings lookup per `Game` and one dict
lookup per decision and hook.

In process mode, a 50-hand heads-up game took about 0.5s, against 0.1s in-process,
including starting the two workers.

### Testing

- New `tests/test_config.py`: precedence of arguments, environment variables and
  `pyproject.toml` (also in a parent directory), per-field resolution, invalid values
  with their source in the message, unknown keys. `config.py` has 100% coverage.
- New `tests/test_isolation.py`:
  - The proof of concept from #101 finds the `Game`, the deck and opponents' holdings
    in-process, and nothing in process mode.
  - All 18 built-in bots play in process mode.
  - Hooks and decisions receive the same sequence in both modes.
  - Timeouts (including a late reply that must be discarded), exceptions, wrong return
    types, invalid actions and a worker that calls `os._exit` all end in a fold and a
    finished game.
  - Unpicklable players and players that can't be loaded in the worker are rejected
    by `add_player`.
  - Workers stop when the game ends, on `remove_player` and on leaving the context
    manager.
  - `get_player_state` returns the same data in both modes, during and after the game,
    and after `remove_player`. It returns a copy, `None` for bots without
    `export_state`, and `None` with a warning when an isolated bot's export raises,
    isn't JSON, isn't a `dict`, or its worker has died. In-process, these errors
    propagate.
  - `set_player_state` restores state in both modes, before a game and in a new game
    from a saved state. It copies the state, raises a `RuntimeError` when an isolated
    import fails or the worker has stopped, and a `TypeError` for invalid states or
    in-process players without `import_state`.
  - The worker loop is also tested in a thread, where coverage can see it.
- New `tests/test_rng.py`:
  - The same seed deals the same cards, and different seeds deal different cards.
  - `game.seed` repeats a game that wasn't seeded explicitly.
  - Seeding `random` before creating a game is still reproducible.
  - Players that consume global random numbers don't change the cards.
  - Isolated and in-process games with the same seed deal the same cards.
  - The seed is not visible in the state or in player views.
  - `Deck` methods with an `rng` are independent of the global `random` module.
- The existing suite passes unchanged. `test_integration_games.py` also passes with
  `MAVERICK_PLAYER_ISOLATION=process`.

### Follow-ups and known limitations

- Code that runs when a bot is created (module import, `__init__`, pickling) still runs
  in the engine's process. Fully untrusted bots would need to be created in the worker
  from an import path and arguments.
- No CPU or memory limits in workers. `resource.setrlimit` in the worker would be a
  simple start on POSIX systems.
- An option to seed the random number generator of each worker for reproducible bot
  decisions.
- Saving and resuming games builds on `export_state`/`import_state` and on the
  engine-owned generator: #103.
- A timeout can't stop a worker that is still computing. Its next decisions wait
  behind the late one and may time out too.
