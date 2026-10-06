---
myst:
  html_meta:
    description: "Players receive a read-only PlayerView instead of the live Game, closing every API-level leak of hidden information."
---

# Players receive a PlayerView instead of the Game

| | |
|---|---|
| **Date** | 2026-10-06 |
| **PR / Issues** | #102, follow-up #101 |
| **Version** | 0.7.0 (unreleased) |
| **Breaking** | Yes |

## Summary

Players used to receive the live `Game` in `decide_action` and in their event hooks, so a
bot could read opponents' hole cards, the upcoming board, other players' strategy
objects, and even change the game. Players now receive a `PlayerView`: a frozen,
per-player copy of the public game state, the rules, the event history and their own hole
cards, with no reference back to the `Game`. Opponents' cards become visible only once
they are shown at showdown. The argument is still called `game`, so all built-in bots
work unchanged. A bot can still reach the `Game` through Python introspection; isolating
bots in separate processes is tracked in #101.

## Details

### Motivation

Everything a bot needed to cheat was one attribute away from the `game` argument:

| Leak | Path |
|---|---|
| Opponents' hole cards | `game.state.players[i].state.holding` |
| The upcoming board | `game.deck` |
| Other players' strategy objects | `game.button`, `game.small_blind`, `game.big_blind` |
| Changing the game | private methods such as `game._update_state` |
| Hole cards in events | `GAME_STATE_CHANGED` `before` / `after` payloads, and `game.history` |
| The `Game` itself | `Player.game`, set by `Game.add_player` |
| Shared mutable objects | `Card`, `Holding.cards` and `PokerRules` shared with the engine |

Results of bot-vs-bot simulations could therefore not be trusted.

### Changes

- **`maverick.playerview`** (new module):
  - `PlayerView`, a frozen dataclass with `player_uid`, `game_uid`, `state`, `rules` and
    `history`, plus `me`, `holding`, `uid` and `get_player_snapshot()`. `from_state()`
    builds one from unredacted data, which is handy in tests.
  - `redact_state()` and `redact_event()`: pure functions that remove unrevealed
    holdings and return copies that share no mutable objects with the engine.
  - `EventHistoryView`: an O(1), fixed-length, read-only window over a player's event
    history.
- **`Game`**:
  - `get_player_view(player)` builds a view. `decide_action` and the `on_event` and
    `on_<event_type>` hooks receive it as `game`. External `EventBus` listeners still
    receive the `Game`.
  - Holdings revealed at showdown are tracked per hand and stay visible until the next
    hand starts.
  - Each player has its own copy of the event history, synced lazily when a view is
    built, and its own copy of the rules.
  - The engine stores its own copy of the action a player returns, so the player can't
    change the recorded action afterwards.
  - Hooks receive their copy of the event by `uid`, so the right event is delivered even
    if an external listener emits another event first.
- **`Player`**: `Player.game` returns the last view the player received, and
  `Player.state` reads from it. The `_game` back-reference is gone.
- **`Card`** is frozen.
- **Type hints** in `Player`, `PlayerLike` and all built-in bots changed from `Game` to
  `PlayerView`.

### Breaking changes and migration

- Code inside a player that uses `Game` members other than `state`, `rules`,
  `get_player_snapshot()`, `history` and `uid` must be updated. In particular there is
  no `game.deck`: use `estimate_holding_strength` or build a `Deck` without the known
  cards.
- `Player.game` is a `PlayerView`. Outside of `decide_action` and the hooks, it shows the
  game as of the player's last decision or event.
- Player hooks receive a copy of the event. In `GAME_STATE_CHANGED` payloads, other
  players' unrevealed holdings are removed.
- `PlayerView.history` doesn't contain `GAME_STATE_CHANGED` events.
- `Card` instances can no longer be modified.

### Design decisions and alternatives considered

The rationale is recorded in {doc}`../design_decisions`, section "Players receive a
PlayerView, not the Game". Decisions made along the way:

- **Keeping the `game=` keyword** instead of adding a new `view=` keyword with a
  deprecation period. The view mirrors the parts of `Game` that bots actually use, so
  most bots keep working. A deprecation period would have left the leak open until the
  old keyword was removed.
- **A plain frozen dataclass instead of a Pydantic model** for `PlayerView`. Pydantic
  would validate, and therefore copy, the history on every view, which grows with the
  game.
- **Freezing `Card` instead of deep-copying the state.** Generic `deepcopy` of the state
  took about 80% of the run time. With frozen cards, only the players list and the
  `Holding.cards` lists need to be copied. `Holding` itself was not frozen, because its
  `cards` list would still be mutable.
- **Leaving `GAME_STATE_CHANGED` out of player histories.** These events only exist while
  an external listener is subscribed, so including them made a bot's history depend on
  unrelated observers. Redacting them for every player also made games with a listener
  about 5× slower. Bots that override `on_event` still receive them, redacted.

### Performance

300 hands with 6 `CallBot`s, compared with `dev`:

| Scenario | `dev` | This change |
|---|---|---|
| No listeners | 0.88s | 1.64s |
| `GAME_STATE_CHANGED` listener | 4.7s | 5.6s |

`CallBot` does almost no work, so this is the worst case. The first working version was
about 14× slower than `dev`. Profiling led to these optimizations:

- Views are not built for players whose `on_event` is the no-op `Player.on_event` default.
  Before, most of the views built were for that.
- `Card` is frozen, so most of the state can be shared (see above).
- Event payloads are copied with a pickle round trip, with `deepcopy` as a fallback, and
  empty payloads are skipped.
- Rules are copied once per player, not per view. An earlier version passed the copy as
  the default argument of `dict.setdefault`, which evaluated it every time.
- `GAME_STATE_CHANGED` events are left out of player histories (see above).

### Testing

- New `tests/test_player_view.py`: opponents' holdings hidden in decisions and hooks;
  revealed holdings visible until the next hand; no `Game`, `Deck` or `Player` reachable
  from a view; changing a view leaves the game unchanged; redacted `GAME_STATE_CHANGED`
  payloads for players but full ones for external listeners; returned actions can't be
  changed afterwards; hooks receive the right event when a listener emits; duck-typed
  players; and unit tests for the redaction functions and `EventHistoryView`.
  `playerview.py` has 100% coverage.
- The existing suite passes without changes.
- A bot that tried every leak path played a 52-hand game against the built-in
  archetypes. It never saw an opponent's holding, and none of the paths were reachable.

### Follow-ups and known limitations

- A bot written to cheat on purpose can still reach the `Game` through introspection,
  for example `sys._getframe(1).f_locals["self"]`. Python has no access control inside a
  process, so guaranteed isolation requires running bots in separate processes: #101.
