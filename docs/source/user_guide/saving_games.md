---
myst:
  html_meta:
    description: "How to save Maverick games to disk, replay them step by step without the players, and resume them after an interruption or a crash."
---

# Saving, Replaying and Resuming Games

A game can be saved to disk while it runs. The save serves two purposes:

- **Replay:** step through a finished or interrupted game, event by event or hand by
  hand, with every player's hole cards, without creating the players.
- **Resume:** load the game, even after a crash, and continue from the end of the last
  completed hand, with the same cards it would have dealt otherwise.

## Saving a game

Pass a directory as `save_dir`:

```python
from maverick import Game, PlayerState
from maverick.players import CallBot, SharkBot

game = Game(small_blind=1, big_blind=2, max_hands=50, save_dir="saves/game-1")
game.add_player(CallBot(name="Alice", uid="alice"), state=PlayerState(stack=200))
game.add_player(SharkBot(name="Bob", uid="bob"), state=PlayerState(stack=200))
game.start()
```

The directory is created when the game starts, and must not hold a saved game already.
Each time a hand ends, the game writes the events of the hand and a checkpoint to
resume from. Saving doesn't change the cards that are dealt. It makes the game slower,
because the full state of the table is stored after every event: in a test with six
players, 100 hands took about 1.0s instead of 0.65s, and the save took about 125 KB per
hand.

Give the players fixed UIDs, as above, if you want to resume the game later: a resumed
game needs players with the same UIDs and names.

## Replaying a game

{class}`~maverick.replay.Replay` reads a save. Every step is one event together with
the full state of the table right after it:

```python
from maverick import GameEventType, Replay

replay = Replay("saves/game-1")
print(len(replay), "steps in hands", replay.hand_numbers)

replay.go_to_hand(3)
while replay.forward():
    event, state = replay.event, replay.state
    if event.type == GameEventType.PLAYER_ACTION_TAKEN:
        print(event.player_uid, event.action.action_type.name, state.pot)
    if event.type == GameEventType.HAND_ENDED:
        break
```

- `forward(steps)` and `backward(steps)` move the cursor and return `False` when it
  can't move any further. `seek(index)` jumps to a step, and `go_to_hand(n)` to the
  start of a hand.
- `hand(n)` returns all `(event, state)` pairs of a hand, and iterating over the replay
  returns all of them.
- `rules`, `seed`, `players` and `game_uid` describe the game.

The states hold the hole cards of every player. To show a hand as a player or a
spectator saw it, remove the holdings with {func}`~maverick.playerview.redact_state`.

A replay never creates a `Game` or any players, so it works without the code of the
bots.

## Resuming a game

{meth}`Game.load <maverick.game.Game.load>` loads a save, and
{meth}`~maverick.game.Game.start` continues it:

```python
game = Game.load(
    "saves/game-1",
    players=[CallBot(name="Alice", uid="alice"), SharkBot(name="Bob", uid="bob")],
)
game.start()
```

- **The players must be supplied,** because the save holds data only, never code. They
  must be the players at the table when the last hand ended, with the same UIDs and
  names. Eliminated players can be left out.
- **Player state is restored** through the `import_state` hook, with what the player
  returned from `export_state` when the last hand ended (see
  {ref}`player-state-export-import`). Players without these hooks
  start fresh. If a player's `export_state` failed when the checkpoint was written,
  the game logs a warning and the player continues without its state.
- **The rules, the seed and `first_button_position` come from the save.** `max_hands`
  does too, unless you pass a new value, for example to continue a game that reached
  its maximum. `player_isolation`, `decision_timeout`, `log_events` and
  `exc_handling_mode` are passed as for a new game.
- **The game continues where the last completed hand ended.** A hand that was
  interrupted is played again from the start, and its events are removed from the
  save. With deterministic players, a game that is interrupted and resumed ends exactly
  like one that wasn't. Isolated players that use the `random` module count as
  deterministic here, because the game seeds them between hands (see
  {ref}`isolated-player-random-numbers`).
- **The resumed game emits a `GAME_RESUMED` event** before the next hand, so listeners
  and players can see where it restarted. The game keeps its UID and its history, and
  keeps writing to the same save, so a replay shows the whole game.

## What a save contains

A save is a directory with three files:

| File | Contents | Used for |
|---|---|---|
| `header.json` | Format version, Maverick version, rules, seed, `max_hands`, and the players at the start | Both |
| `events.jsonl` | One line per event, with the state of the table after it | Replay |
| `checkpoint.json` | The table, the state, the state of the random number generator, and what each player exported, at the end of the last completed hand | Resume |

- **Everything is JSON.** Loading never unpickles anything and never imports code named
  in the save, so a save from someone else can't run code on your machine.
- **Saves are written safely.** The events of a hand reach the disk only once the hand
  is over, and the checkpoint is written to a temporary file that then replaces the old
  one, so a crash can't leave a broken checkpoint behind.
- **Saves are versioned.** Loading a save written in a format this version of Maverick
  doesn't read fails with a {class}`~maverick.savegame.SaveFormatError` that says so.
- `GAME_STATE_CHANGED` events are not saved, since the state is stored with every event.

## Keep saves of running games secret

While a game runs, its save gives away information the players must not have: the
checkpoint holds the state of the random number generator, from which the cards of the
next hand can be computed. Maverick creates the directory and the files so that only
your operating system user can read them.

Players isolated in worker processes run as the same user, though, so a malicious bot
can read the checkpoint and predict the cards. When you save games with bots you don't
trust, run the game in a container or as a separate operating system user, and keep the
save directory out of the workers' reach (see {doc}`player_isolation`). Once the game is
over, the save can be shared freely.
