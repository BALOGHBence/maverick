# Design Decisions

This page records key architectural decisions made during development, the reasoning
behind them, and the trade-offs accepted. It is intended to help contributors understand
*why* the codebase looks the way it does and to prevent well-intentioned refactors from
accidentally undoing deliberate choices.

---

## GameState Immutability

### Decision

`GameState` is a frozen Pydantic model (`frozen=True`). All state transitions create a
new `GameState` instance via `model_copy(update=...)` through the internal
`Game._update_state(**changes)` helper. Direct field assignment on a live `GameState`
instance raises a `ValidationError`.

### Rationale

- **Snapshot integrity** — Event listeners subscribed to `GAME_STATE_CHANGED` receive
  `before`/`after` dicts that are true point-in-time snapshots (`model_dump(mode="json")`
  at the moment of transition), not live references that could mutate underneath the
  listener.
- **Auditability** — A single entry point for all state changes makes the game engine
  easier to reason about and debug.
- **Safety** — Prevents accidental field assignment by player strategies or external code
  that receives a `game.state` reference.

### Trade-offs

`frozen=True` is only *shallow* immutability. Mutable objects contained in `GameState`
(player objects, the community cards list, the deck) are not protected by the freeze.
The roadmap below addresses this progressively.

### Roadmap to full (deep) immutability

The following steps are planned, each as a separate PR:

| Step | Change | Breaking? |
| --- | --- | --- |
| 1 | Freeze `PlayerState` + introduce `_update_player_state` helper | No |
| 2 | ✅ Introduce `PlayerSnapshot`; decouple strategy objects from `GameState` | **Yes** |
| 3 | Replace `community_cards` in-place mutations with `_update_state` calls | No |
| 4 | ✅ Move `Deck` out of `GameState` into `Game._deck` | **Yes** |

See [SPEC.md](../../../../SPEC.md) at the repository root for the full specification.

---

## Deck is not part of GameState

*(Implemented — see roadmap Step 4 above)*

### Decision

The `Deck` will be held by `Game._deck`, not stored as a field on `GameState`. A
read-only `game.deck` property will expose it for bots that need it for Monte Carlo
simulations.

### Rationale

- **Observable state vs. engine internals** — `GameState` represents the observable state
  of the poker table: pot, community cards, player stacks, positions. The remaining cards
  in the deck are not observable to any player in a real game; they are a private
  implementation detail of the dealer.
- **Snapshot integrity** — Serializing a `GameState` snapshot (e.g., for the
  `GAME_STATE_CHANGED` `before`/`after` payload) currently leaks which cards remain in
  the deck. Moving the deck out eliminates this information leak.
- **Simplicity** — Keeping the `Deck` in `Game._deck` lets it remain a mutable object
  without compromising `GameState` immutability semantics.

### Alternative considered

Making `Deck` immutable (functional style: `dealt_cards, new_deck = deck.deal(n)`).
Rejected because it adds object-allocation overhead on every deal with no benefit — the
deck is never part of a snapshot that needs to be independently preserved.

---

## PlayerSnapshot — Decoupling strategy from observable state

*(Implemented — see roadmap Step 2 above)*

### Decision

`GameState.players` now holds `list[PlayerSnapshot]`, where `PlayerSnapshot` is a frozen
Pydantic model containing only observable data (`uid`, `name`, `state: PlayerState`).
Strategy objects (`decide_action`, `on_event`) are held separately in
`Game._strategies: dict[str, PlayerLike]`.

`Table._seats` was changed from `list[Optional[PlayerLike]]` to `list[Optional[str]]`
(player UIDs). `Table.next_occupied_seat` now accepts an explicit `active_uids: set[str]`
parameter instead of reading `player.state.state_type` directly, so Table has no
dependency on live state at all.

`Game._update_player_state` now creates fresh `PlayerSnapshot` instances via `model_copy`;
it never mutates any live strategy object. As a result consecutive `GameState` instances
produced by `_update_state` share no mutable player references.

Custom player strategies access their own current state via
`game.get_player_snapshot(self.uid)` rather than `self.state`, because the engine no
longer writes back to strategy objects.

### Rationale

- **True snapshot isolation** — With live player objects in `GameState.players`, mutating
  `player.state` retroactively changed every prior `GameState` instance that referenced
  the same player object. `PlayerSnapshot` breaks this coupling: each `GameState` holds
  independent frozen copies.
- **Separation of concerns** — Strategy logic (how a player decides) is distinct from
  observable data (what a player's current stack is). Mixing them in a single object
  makes both harder to evolve independently.
- **`Table` simplification** — Table now navigates by UID instead of object reference,
  eliminating synchronisation bugs between `Table` and `GameState`.

### Trade-offs

This is a **breaking change** to the public API:
- `GameState.players` no longer returns objects with `decide_action`. Code that reads
  state (`p.state.stack`, `p.uid`, etc.) is unaffected; code that calls strategy methods
  must go through `Game._strategies`.
- `Table[seat]` now returns a UID string, not a `PlayerLike`.
- `Table.next_occupied_seat(active=True)` is replaced by
  `Table.next_occupied_seat(active_uids={...})`.
- Custom players that relied on `self.state` inside `decide_action` must instead use
  `game.get_player_snapshot(self.uid)`.

---

## GAME_STATE_CHANGED event and lazy serialization

### Decision

`_update_state` only calls `model_dump(mode="json")` when at least one handler is
subscribed to `GAME_STATE_CHANGED`. The guard uses `EventBus.has_subscribers(event_type)`
before allocating the `before`/`after` dicts.

### Rationale

`model_dump` on a `GameState` that contains many players is non-trivial. Most games run
without a `GAME_STATE_CHANGED` listener; paying the serialization cost unconditionally on
every state transition would be wasteful. The `has_subscribers` guard reduces the overhead
to a single `any()` call over the subscriber list when no listeners are registered.
