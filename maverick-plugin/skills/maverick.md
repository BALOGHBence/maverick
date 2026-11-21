---
name: maverick
description: General-purpose guide for writing code with the Maverick poker library — custom players, game setup, seeding, player isolation in worker processes, player state export/import, events and subscriptions, built-in listeners, game histories, and saving, replaying, loading and resuming games. Auto-invoked when the user wants to write, run, or debug code that uses Maverick.
---

You are writing code that uses the Maverick poker library (Python >= 3.12). It is published on PyPI as `maverick`: install it with `pip install maverick` (or `uv add maverick`) and import it as `import maverick`.

## 1. Custom players — the contract

Subclass `maverick.Player` (or duck-type `maverick.PlayerLike`: needs `uid: str`, `name: str`, `decide_action`).

```python
from maverick import Player, PlayerAction, PlayerView, ActionType

class MyBot(Player):
    cls_uid = "…32-char hex…"  # optional: stable id for Player.get_by_uid()

    def decide_action(
        self,
        *,
        game: PlayerView,
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_uid=self.uid, action_type=ActionType.CHECK)
        if ActionType.CALL in valid_actions:
            return PlayerAction(player_uid=self.uid, action_type=ActionType.CALL)
        return PlayerAction(player_uid=self.uid, action_type=ActionType.FOLD)  # always valid
```

Contract rules:
- All arguments are **keyword-only**. Accept unused ones with `**_`.
- Return a `PlayerAction(player_uid=self.uid, action_type=..., amount=...)`. Only choose from `valid_actions`; end with a FOLD fallback (FOLD is always valid).
- `amount` is **chips moved from the stack into the pot now** — see section 2 before writing any BET/RAISE logic.
- An invalid action (wrong type, too small, not your turn) is **converted to FOLD** with a warning — it does not raise.
- Players are strategies, not state holders: the engine owns all state. `game.state.players` holds frozen `PlayerSnapshot`s (`uid`, `name`, `state`), not your player objects.
- `PlayerAction.payload` may carry extra dict data; `decision_time_seconds` is filled by the engine.
- Constructor is keyword-only: `MyBot(name="Bob", uid=None)`. Names and uids must be unique per game. When overriding `__init__`, forward `**kwargs` to `super().__init__`. Pass a fixed `uid` if the game may be resumed later (section 9).
- Optional state hooks: `export_state(self) -> dict | None` returns everything needed to restore the bot (statistics, opponent models, …) as a JSON-serializable dict; `import_state(self, state: dict) -> None` restores it. Leave out secrets and anything recreatable (clients). They are the only way to get data out of an isolated bot (section 8) and are what a resumed game restores (section 9).
- Write bots so they also work under process isolation: define the class at module top level (not in a function or notebook), keep it picklable, and don't rely on mutating shared objects outside the bot.
- Useful inside `decide_action`: `self.state` (`PlayerState`: `stack`, `current_bet`, `total_contributed`, `holding.cards`, `state_type`, `seat`), `game.state` (`GameState`: `street`, `pot`, `current_bet`, `min_bet`, `last_raise_size`, `community_cards`, `small_blind`, `big_blind`, `hand_number`, `players`, `get_players_in_hand()`, `get_active_players()`), `game.rules.showdown.hole_cards_required`, `game.holding` (own hole cards). `game` is a read-only `PlayerView`: opponents' `holding` is `None` until revealed at showdown and there is no `game.deck`. `self.state` only works for `Player` subclasses; duck-typed players use `game.get_player_snapshot(self.uid).state`.
- Hand evaluation (scores only compare hands; strength is a win probability):
  - `maverick.utils.score_hand(cards)` → `(HandType, score)` for up to 5 cards; `Holding(cards=...).score()`, `Hand(private_cards=..., community_cards=...).score()` do the same.
  - `maverick.utils.find_highest_scoring_hand(private, community, n_private=...)` → `(cards, HandType, score)`.
  - `maverick.utils.estimate_holding_strength(private, community_cards=..., n_simulations=..., n_private=..., n_players=...)` → win probability via Monte Carlo (slow; keep `n_simulations` modest). Same via `Holding.estimate_strength(...)`.
  - Pass `n_private=game.rules.showdown.hole_cards_required` so Omaha (2) is evaluated correctly.
  - Cards: `Card(suit=Suit.HEARTS, rank=Rank.ACE)`, `card.code()` → `"Ah"`; `Deck.build().shuffle().deal(n)`.
- Built-in bots in `maverick.players`: `FoldBot`, `CallBot`, `AggressiveBot`, plus archetypes (`TightAggressiveBot`, `LooseAggressiveBot`, `TightPassiveBot`, `LoosePassiveBot`, `ManiacBot`, `TiltedBot`, `BullyBot`, `GrinderBot`, `GTOBot`, `SharkBot`, `FishBot`, `ABCBot`, `HeroCallerBot`, `ScaredMoneyBot`, `WhaleBot`).

## 2. Betting semantics

Get this right or your bot's actions get turned into folds.

**`PlayerAction.amount` is "raise-by / chips-to-add"**: the chips moved from the stack to the pot by this action, on top of what the player already put in this street. It is **not** "raise-to", **not** the pot after the action, and **not** the raise increment.

| Action | When valid | `amount` |
| --- | --- | --- |
| CHECK | player's street bet == table bet | omit |
| CALL | there is a bet to match | omit; engine adds the difference (short stack → ALL_IN) |
| BET | table bet == 0 on this street (never pre-flop: blinds count as a bet) | `>= min_bet_amount` (the big blind) |
| RAISE | table bet > 0 and stack covers a full min raise | `>= min_raise_amount`; includes the call portion |
| ALL_IN | stack > 0 | omit; engine adds the whole stack |

The **raise increment** (how much the table bet grows) must be at least the previous increment (`game.state.last_raise_size`); the big blind sets the first one. `min_raise_amount = table bet + last_raise_size − player's street bet`.

Example, pre-flop, BB=20, player has put in 0: `RAISE amount=40` → 20 to call + 20 increment → table bet 40, increment 20. The next player with 0 in must add at least 60 to raise (40 to call + 20).

Other rules:

- **Heads-up**: the button posts the small blind and acts first pre-flop; the big blind acts first on later streets. With 3+ players, SB/BB are left of the button and UTG (left of BB) acts first pre-flop.
- **Short all-in** (all-in that raises by less than the minimum increment): the table bet goes up but `last_raise_size` does not change and betting is **not reopened** — players who already acted only face the extra amount. A full-size all-in raise reopens betting.
- A betting round ends when one player is left, nobody can act (all ALL_IN), or every ACTIVE player has acted since the last reopen and matched the table bet.
- Only No-Limit games are supported; antes are posted by every player.

## 3. Setting up and starting games

```python
from maverick import Game, PlayerState
from maverick.players import CallBot, AggressiveBot

game = Game(small_blind=10, big_blind=20, max_hands=10)
game.add_player(CallBot(name="Alice"), state=PlayerState(stack=1000))
game.add_player(AggressiveBot(name="Bob"), state=PlayerState(stack=1000, seat=3))
game.start()  # runs synchronously until max_hands or one player remains

for s in game.state.players:  # includes eliminated players
    print(s.name, s.state.stack, s.state.state_type)
```

- `Game(...)` keyword args: `small_blind`, `big_blind`, `ante`, `min_players=2`, `max_players`, `max_hands=1000`, `exc_handling_mode="log" | "raise"` (raise = handler exceptions propagate), `log_events=True`, `rules: PokerRules | None`, `first_button_position: int | None` (drawn by card draw if `None`), `seed: int | None`, `player_isolation: "none" | "process" | None` and `decision_timeout: float | None` (section 8), `save_dir: str | PathLike | None` (section 9).
- `Game` is a context manager (`with Game(...) as game:`); leaving it, or `game.close()`, stops isolated players' worker processes. Use it whenever isolation might be on.
- Without a `state`, a player gets a stack of **0** — always pass `PlayerState(stack=...)` (or a dict).
- Always set a sensible `max_hands`, especially with passive bots like `FoldBot`, or games run for a long time.
- `game.state.players` keeps eliminated players (`state_type=ELIMINATED`, `stack=0`); use `game.state.get_non_eliminated_players()` / `get_active_players()` to filter.
- `game.game_uid` is `None` before `start()` and gets a new value on every start — use it to tell sessions apart. A game continued with `Game.load` keeps its UID.
- Players can only be added before `start()`; remove with `game.remove_player(p)` between hands / after the game.
- Constructor args override the matching `rules` fields. Omaha example:

```python
from maverick.rules import PokerRules, DealingRules, StakesRules, ShowdownRules

rules = PokerRules(
    dealing=DealingRules(hole_cards=4),
    stakes=StakesRules(small_blind=5, big_blind=10),
    showdown=ShowdownRules(hole_cards_required=2),  # 0 = Hold'em
)
game = Game(rules=rules)
```

- Reproducibility: pass `seed=...` to `Game`. The game has its own random generator (read it back with `game.seed`) that shuffles and draws the button; same seed + same players + same decisions → same cards. Bots' use of `random` no longer changes the cards. Without `seed`, one is drawn from the global `random` module when the game is created, so `random.seed(...)` **before** `Game(...)` still works, but seeding afterwards has no effect on the cards.
- In-process bots share your script's `random` module; seed it yourself if their decisions must be reproducible. Isolated bots are seeded by the game (section 8).
- Silence engine logs with `log_events=False`, or via `logging.getLogger("maverick")`.

## 4. Events and subscribing

Event types: `maverick.GameEventType` — `GAME_STARTED`, `GAME_ENDED`, `HAND_STARTED`, `HAND_ENDED`, `HOLE_CARDS_DEALT`, `BLINDS_POSTED`, `ANTES_POSTED`, `BETTING_ROUND_STARTED`, `BETTING_ROUND_COMPLETED`, `PLAYER_ACTION_TAKEN`, `FLOP_DEALT`, `TURN_DEALT`, `RIVER_DEALT`, `SHOWDOWN_STARTED`, `SHOWDOWN_COMPLETED`, `PLAYER_CARDS_REVEALED`, `POT_WON`, `PLAYER_JOINED`, `PLAYER_LEFT`, `PLAYER_ELIMINATED`, `GAME_STATE_CHANGED`, `GAME_RESUMED` (a loaded game continues; emitted by `start()` before the next hand).

**Explicit listeners** — any callable `handler(event: GameEvent, game: Game) -> None`:

```python
token = game.subscribe(
    GameEventType.POT_WON,
    handler,
    priority=0,   # higher runs first
    once=False,   # auto-unsubscribe after first call
    mask=None,    # optional predicate(event) -> bool
)
game.unsubscribe(token)
```

- One subscription = one event type. To listen to everything: `for t in GameEventType: game.subscribe(t, handler)`.
- Subscribe **before** `game.start()`; dispatch is synchronous. Subscribing/unsubscribing inside a handler is safe.
- Handler exceptions are logged and swallowed unless `exc_handling_mode="raise"`.
- Handlers receive the live `game` and could mutate it — treat it as read-only. Listeners always run in the engine's process, also with player isolation, so they work the same in both modes.

**Player hooks** (run after explicit listeners, exceptions always logged):
- `on_event(self, event, game)` — called for every event.
- Implicit `on_<event_type_lowercase>(self, event, game)`, e.g. `on_hand_started`, `on_pot_won`, `on_game_ended`.
- Hooks receive a `PlayerView` (not the `Game`) and a copy of the event; `GAME_STATE_CHANGED` payloads have other players' unrevealed holdings removed.

## 5. Reading events

`GameEvent` is a frozen Pydantic model:

| Field | Meaning |
| --- | --- |
| `type` | `GameEventType` |
| `uid`, `ts` | event id, epoch timestamp |
| `hand_number` | current hand |
| `street`, `stage` | `Street` / `GameStage` or `None` |
| `player_uid` | involved player (actions, joins, wins, eliminations, reveals) |
| `action` | `PlayerAction` for `PLAYER_ACTION_TAKEN` |
| `payload` | event-specific dict |

Payloads:
- `POT_WON`: `{"amount": int}` (with `player_uid`).
- `PLAYER_CARDS_REVEALED`: `{"holding": [codes], "best_hand": [codes], "best_hand_type": str, "best_score": float}` — only emitted when the pot is contested at showdown.
- `GAME_STATE_CHANGED`: `{"before": dict, "after": dict}` (full `GameState.model_dump(mode="json")`). Very frequent.

The event is a snapshot of *what* happened; for the table context read `game.state` inside the handler (pot, bets, stacks are already updated). Map `player_uid` to a name via `{p.uid: p.name for p in game.state.players}`. `event.model_dump(mode="json")` gives a JSON-safe dict (enums become their int values).

## 6. Built-in listeners (`maverick.listeners`)

Both take an optional `game` in the constructor, or attach later with `.listen(game)`. Attach **after** adding players and **before** `start()`.

- **`GameTranscriber(game)`** — subscribes to all events and builds a human-readable transcript.
  - `.history` → `str` transcript (blinds, positions, every action with pot/bet, street summaries, showdown, winners, eliminations).
  - `.event_dump` → `list[dict]` of `event.model_dump(mode="json")`.
- **`GameStateCollector(game, event_types=None)`** — appends `game.state.model_dump(mode="json")` plus `ts` and `event_uid` to `.states` on each event (all types if `event_types` is `None`; raises `TypeError` for non-`GameEventType` entries).

```python
from maverick.listeners import GameStateCollector
collector = GameStateCollector(game, event_types=[GameEventType.HAND_ENDED])
game.start()
stacks_per_hand = [[p["state"]["stack"] for p in s["players"]] for s in collector.states]
```

## 7. Game history

**With `GameTranscriber`** (e.g. text history for an LLM):

```python
from maverick.listeners import GameTranscriber

transcriber = GameTranscriber(game)
game.start()
print(transcriber.history)           # readable text
df = pd.DataFrame(transcriber.event_dump)  # tabular; enum columns are ints
df["type_name"] = df["type"].map({e.value: e.name for e in GameEventType})
```

Inside `decide_action`, read past events from `game.history` (the player's redacted history, see below). Don't hand a transcriber or collector to a player: they hold the full `Game`, which would leak hidden information.

**Without `GameTranscriber`:**
- `game.history` → `list[GameEvent]` of every emitted event, in order; always recorded, no setup needed.
- In player code, `game` is a `PlayerView` and `game.history` is a read-only sequence of copies of the same events, without `GAME_STATE_CHANGED`.

```python
for e in game.history:
    if e.type == GameEventType.PLAYER_ACTION_TAKEN:
        print(e.hand_number, e.street.name, e.player_uid, e.action.action_type.name, e.action.amount)
```

- Or write your own listener that formats/stores what you need:

```python
class EventRecorder:
    def __init__(self) -> None:
        self.events: list[GameEvent] = []

    def record(self, event: GameEvent, game: Game) -> None:
        self.events.append(event)

recorder = EventRecorder()
for t in GameEventType:
    game.subscribe(t, recorder.record)
```

- For state snapshots rather than events, use `GameStateCollector` (section 6).

## 8. Player isolation (worker processes)

By default bots run in the engine's process. A malicious bot can then reach the engine through introspection (`sys._getframe`, `gc.get_objects()`) and read the deck. For bots you don't trust, run each player in its own worker process:

```python
from maverick import Game, PlayerState
from maverick.players import CallBot, SharkBot

if __name__ == "__main__":  # required: workers are started with "spawn"
    with Game(small_blind=1, big_blind=2, player_isolation="process", decision_timeout=5.0) as game:
        game.add_player(CallBot(name="Alice"), state=PlayerState(stack=200))
        game.add_player(SharkBot(name="Bob"), state=PlayerState(stack=200))
        game.start()
```

- Modes: `"none"` (default, fast) and `"process"`; also `maverick.PlayerIsolation.NONE` / `.PROCESS`.
- Settings resolve per setting from: `Game` argument → env vars `MAVERICK_PLAYER_ISOLATION` / `MAVERICK_DECISION_TIMEOUT` → `[tool.maverick]` table in the nearest `pyproject.toml` (`player_isolation = "process"`, `decision_timeout = 5.0`). Invalid values or unknown keys raise `ValueError`. Resolved values: `game.settings`.
- `decision_timeout` (seconds) applies only to isolated players; a late player folds and its answer is discarded.
- An isolated player that times out, raises in `decide_action`, returns an invalid action, or whose worker dies **folds** with a warning instead of stopping the game (a dead worker folds every remaining hand).
- Requirements: players must be picklable and their class importable in a fresh interpreter (no classes defined in functions, notebooks or the REPL — `add_player` raises `TypeError`/`RuntimeError`); scripts need the `if __name__ == "__main__":` guard.
- **The bot lives in the worker.** The object you passed to `add_player` is a copy that is never updated (except `Player.game`, the latest view). Reading `bot.some_counter` after the game gives the initial value. Get data out with state hooks:

```python
saved = game.get_player_state(bot)   # calls export_state (in the worker if isolated) → dict | None
game.set_player_state(bot, saved)    # calls import_state
```

  - Works the same in both modes, always through a JSON round trip. Callable between hands (e.g. from a listener) or before/after the game.
  - When a worker stops (player left/eliminated, game ended), it exports once more; `get_player_state` keeps returning that, while `set_player_state` then raises `RuntimeError`.
  - Isolated: a failing/timing-out `export_state` → warning and `None`; a failing `import_state` → `RuntimeError`. In-process, hook exceptions propagate.
- Random numbers: before each hand the game seeds the worker's global `random` (and `numpy`'s legacy global generator if imported) from the game seed, the player's UID and the hand number. Isolated bots using `random` are therefore reproducible with `Game(seed=...)`, also across save/resume. A bot that seeds `random` itself gets reseeded next hand — use its own `random.Random(...)` / `numpy.random.default_rng(...)` instead.
- Slower: every decision and hook crosses a process boundary; `decision_time_seconds` includes that overhead.
- Not a sandbox: workers run as the same OS user, inherit env vars (secrets!), and can use files and the network. For fully untrusted code, also use a container / separate user, and strip secrets from the environment. Bot import and `__init__` still run in your process.

## 9. Saving, replaying and resuming games

**Save** by passing `save_dir` (created at start; must not already hold a save). After every hand the game writes the hand's events, each with the full table state after it, plus a checkpoint to resume from. It doesn't change the cards dealt, but is slower (~1.5×). Use fixed player UIDs if you want to resume.

```python
game = Game(small_blind=1, big_blind=2, max_hands=50, seed=42, save_dir="saves/game-1")
game.add_player(CallBot(name="Alice", uid="alice"), state=PlayerState(stack=200))
game.add_player(SharkBot(name="Bob", uid="bob"), state=PlayerState(stack=200))
game.start()
```

**Replay** with `maverick.Replay` — no `Game`, no players, no bot code needed:

```python
from maverick import GameEventType, Replay

replay = Replay("saves/game-1")
print(len(replay), replay.hand_numbers, replay.seed, replay.rules, replay.players)
replay.go_to_hand(3)
while replay.forward():
    event, state = replay.event, replay.state  # GameEvent, GameState right after it
    if event.type == GameEventType.HAND_ENDED:
        break
```

- Navigation: `forward(steps=1)` / `backward(steps=1)` (return `False` at the ends), `seek(index)`, `go_to_hand(n)`, `position`; `hand(n)` → `list[(event, state)]`; iterating yields all pairs; `state_at(index)`; `events`, `game_uid`, `header`.
- Replay states contain **every player's hole cards**; hide them with `maverick.playerview.redact_state(state, viewer_uid, revealed=frozenset())` to show what one player saw.

**Resume** (also after a crash) with `Game.load`, then `start()`:

```python
game = Game.load(
    "saves/game-1",
    players=[CallBot(name="Alice", uid="alice"), SharkBot(name="Bob", uid="bob")],
    max_hands=100,  # optional: raise the limit to continue a finished game
)
game.start()  # emits GAME_RESUMED, then continues from the end of the last completed hand
```

- Supply the players seated when the last hand ended, with the **same UIDs and names** (eliminated ones may be omitted), else `ValueError`. The save holds data only, never code.
- Each player's state is restored via `import_state` with what `export_state` returned at that checkpoint; players without the hooks start fresh.
- Rules, seed and `first_button_position` come from the save; `max_hands` too unless passed. `player_isolation`, `decision_timeout`, `log_events`, `exc_handling_mode` are passed as for a new game. Add listeners after `load` and before `start`.
- An interrupted hand is replayed from its start (its partial events are dropped). With deterministic bots, a resumed game ends exactly like an uninterrupted one, with the same cards. The game keeps its `game_uid`, history and save directory.
- Save files: `header.json`, `events.jsonl` (no `GAME_STATE_CHANGED`), `checkpoint.json`. All versioned JSON — loading never unpickles or imports code; an unreadable or unsupported save raises `maverick.SaveFormatError`.
- Security: a running game's checkpoint holds the RNG state and predicts the next cards. Files are owner-readable only, but isolated bots run as the same user — keep saves of games with untrusted bots out of their reach. Finished saves can be shared.

## 10. When this is not enough

If the question cannot be answered from this skill alone, use the **maverick-docs** skill from this plugin, which looks up the answer in the online documentation at https://pymaverick.readthedocs.io/en/latest/.
