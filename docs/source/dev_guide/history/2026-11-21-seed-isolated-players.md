---
myst:
  html_meta:
    description: "The game seeds the random number generators of isolated players from its seed, the player and the hand, so isolated games and resumed games make the same decisions."
---

# Seeding the random number generators of isolated players

| | |
|---|---|
| **Date** | 2026-11-21 |
| **PR / Issues** | closes #108 |
| **Version** | 0.7.0 (unreleased) |
| **Breaking** | No |

## Summary

With process isolation, every bot runs in a fresh interpreter with its own random
state, so bots that use random numbers made different decisions on every run, whatever
the caller seeded. The game now seeds the global `random` module of every worker, and
`numpy`'s legacy global generator if the bot has imported `numpy`, before the bot is
loaded and again between hands. The seed is derived from the game's seed,
the player's UID and the hand number. Isolated games with the same seed now make the
same decisions, different seeds make different ones, and a saved game that is resumed
plays out exactly like one that was never interrupted, without saving any random state
of the workers.

## Details

### Motivation

Issue #108: `Game(seed=...)` made the cards reproducible in both isolation modes (#109),
but not the decisions of isolated bots that use `random`. That also kept saved games
(#103, #111) from being re-run or resumed exactly when such bots played.

### Changes

- **`maverick._isolation.proxy`**: new `derive_player_seed(game_seed, player_uid,
  hand_number)`, which takes the first 8 bytes of a SHA-256 hash. `ProcessPlayer` takes
  an optional `seed`, which is passed to the worker, and has a new `reseed(seed)`
  method that sends a `("seed", seed)` message without waiting for a reply.
- **`maverick._isolation.worker`**: new `seed_random(seed)`, which seeds `random` and,
  if `numpy` is already imported, `numpy.random.seed(seed % 2**32)`. `run_worker`
  takes an optional `seed` and applies it before unpickling the player, and handles the
  `seed` message.
- **`Game`**: workers are started with the seed of the current hand, in `add_player`
  and when a game is loaded. `_continue_between_hands` reseeds every worker for the
  coming hand. It runs right after the checkpoint is written, and in a loaded game
  right after `GAME_RESUMED`, so everything after the checkpoint, including the
  `GAME_STATE_CHANGED` event of the button move, uses the same random numbers in a
  resumed game as in one that ran through.
- **Documentation**: new section "Random numbers in isolated players" in the player
  isolation guide, which replaces the limitation listed under "What process isolation
  doesn't cover"; updates to the reproducibility and saving guides; new subsection in
  {doc}`../design_decisions`.

### Design decisions and alternatives considered

See "Isolated players are reseeded every hand" in {doc}`../design_decisions`. In short:

- **Reseeding per hand** instead of seeding once per worker and saving each worker's
  random state in checkpoints. It needs no change to the save format and doesn't trust
  state reported by workers.
- **On by default,** answering the open question of the issue. There is no setting to
  turn it off; a bot that wants its own sequence can use its own generator.
- **No `self.rng` on `Player`.** Existing bots use the global `random` module; a
  dedicated generator can be added later without breaking anything.
- **No public API for the per-worker seeds.** The issue proposed exposing them for
  saved games, but they follow from the game seed, which the save already records.

### Performance

One extra message per isolated player and hand, sent without waiting for an answer.
`numpy` is never imported by the worker.

### Testing

`tests/test_player_seeds.py` plays isolated games with bots that fold, check, call and
raise at random:

- same seed, same decisions and draws (also in the bots' `on_hand_started` hook);
- different seed, different draws; different players, different draws;
- a game saved after 3 hands and resumed to 6 makes the same decisions in hands 4–6 as
  a game played through, also with a bot that draws when the button moves between
  hands and uses that number in its next decision.

Unit tests cover the derivation (a pinned value, so it can't silently become
interpreter-dependent), `seed_random` with a fake `numpy`, and the worker loop's
handling of the seed. Removing the per-hand reseed makes the resume tests fail;
reseeding when the hand starts instead of right after the checkpoint makes the test
with draws between hands fail; removing both seeds makes the same-seed test fail too.

### Follow-ups and known limitations

- Random numbers drawn in `on_game_resumed` come from the seed of the last completed
  hand. An uninterrupted game has no such hook call, so there is nothing to match.
- Generators other than `random` and `numpy`'s legacy global one, such as a bot's own
  `random.Random()` seeded from the operating system, are not reproducible.
