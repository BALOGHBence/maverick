---
name: maverick
description: General-purpose guide for writing code with the Maverick poker library — custom players, game setup, events and subscriptions, built-in listeners, and game histories. Auto-invoked when the user wants to write, run, or debug code that uses Maverick.
---

You are writing code that uses the Maverick poker library (Python >= 3.12). It is published on PyPI as `maverick`: install it with `pip install maverick` (or `uv add maverick`) and import it as `import maverick`.

## 1. Custom players — the contract

Subclass `maverick.Player` (or duck-type `maverick.PlayerLike`: needs `uid: str`, `name: str`, `decide_action`).

```python
from maverick import Game, Player, PlayerAction, ActionType

class MyBot(Player):
    cls_uid = "…32-char hex…"  # optional: stable id for Player.get_by_uid()

    def decide_action(
        self,
        *,
        game: Game,
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
- Constructor is keyword-only: `MyBot(name="Bob", uid=None)`. Names and uids must be unique per game. When overriding `__init__`, forward `**kwargs` to `super().__init__`.
- Useful inside `decide_action`: `self.state` (`PlayerState`: `stack`, `current_bet`, `total_contributed`, `holding.cards`, `state_type`, `seat`), `game.state` (`GameState`: `street`, `pot`, `current_bet`, `min_bet`, `last_raise_size`, `community_cards`, `small_blind`, `big_blind`, `hand_number`, `players`, `get_players_in_hand()`, `get_active_players()`), `game.rules.showdown.hole_cards_required`. `self.state` only works for `Player` subclasses; duck-typed players use `game.get_player_snapshot(self.uid).state`.
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

- `Game(...)` keyword args: `small_blind`, `big_blind`, `ante`, `min_players=2`, `max_players`, `max_hands=1000`, `exc_handling_mode="log" | "raise"` (raise = handler exceptions propagate), `log_events=True`, `rules: PokerRules | None`, `first_button_position: int | None` (random if `None`).
- Without a `state`, a player gets a stack of **0** — always pass `PlayerState(stack=...)` (or a dict).
- Always set a sensible `max_hands`, especially with passive bots like `FoldBot`, or games run for a long time.
- `game.state.players` keeps eliminated players (`state_type=ELIMINATED`, `stack=0`); use `game.state.get_non_eliminated_players()` / `get_active_players()` to filter.
- `game.game_uid` is `None` before `start()` and gets a new value on every start — use it to tell sessions apart.
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

- Reproducibility: call `random.seed(...)` before creating/starting the game and set `first_button_position`.
- Silence engine logs with `log_events=False`, or via `logging.getLogger("maverick")`.

## 4. Events and subscribing

Event types: `maverick.GameEventType` — `GAME_STARTED`, `GAME_ENDED`, `HAND_STARTED`, `HAND_ENDED`, `HOLE_CARDS_DEALT`, `BLINDS_POSTED`, `ANTES_POSTED`, `BETTING_ROUND_STARTED`, `BETTING_ROUND_COMPLETED`, `PLAYER_ACTION_TAKEN`, `FLOP_DEALT`, `TURN_DEALT`, `RIVER_DEALT`, `SHOWDOWN_STARTED`, `SHOWDOWN_COMPLETED`, `PLAYER_CARDS_REVEALED`, `POT_WON`, `PLAYER_JOINED`, `PLAYER_LEFT`, `PLAYER_ELIMINATED`, `GAME_STATE_CHANGED`.

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
- Handlers receive the live `game` and could mutate it — treat it as read-only.

**Player hooks** (run after explicit listeners, exceptions always logged):
- `on_event(self, event, game)` — called for every event.
- Implicit `on_<event_type_lowercase>(self, event, game)`, e.g. `on_hand_started`, `on_pot_won`, `on_game_ended`.

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

A player can read a live transcript mid-game (e.g. inside `decide_action`) by keeping a reference to a transcriber attached to the same game.

**Without `GameTranscriber`:**
- `game.history` → `list[GameEvent]` of every emitted event, in order; always recorded, no setup needed.

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

## 8. When this is not enough

If the question cannot be answered from this skill alone, use the **maverick-docs** skill from this plugin, which looks up the answer in the online documentation at https://pymaverick.readthedocs.io/en/latest/.
