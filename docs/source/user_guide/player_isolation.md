---
myst:
  html_meta:
    description: "How to run Maverick players in separate worker processes, so untrusted bots can't reach the game engine, and how to configure it."
---

# Player Isolation

Players never receive the live `Game`, only a {class}`~maverick.playerview.PlayerView`
(see {doc}`custom_players`). By default, though, players run in the same Python process
as the engine. A bot written to cheat on purpose can still reach the engine through
interpreter introspection, for example `sys._getframe` or `gc.get_objects()`, and read
the deck or the hole cards of its opponents.

If you run bots you didn't write yourself, for example in a bot tournament, run every
player in its own worker process:

```python
from maverick import Game, PlayerState
from maverick.players import CallBot, SharkBot

if __name__ == "__main__":
    with Game(small_blind=1, big_blind=2, player_isolation="process") as game:
        game.add_player(CallBot(name="Alice"), state=PlayerState(stack=200))
        game.add_player(SharkBot(name="Bob"), state=PlayerState(stack=200))
        game.start()
```

In process mode, the engine sends each worker a serialized copy of the player's view and
receives the action back as JSON. The worker shares no memory with the engine, so there
is no `Game`, deck or hidden holding in it to find.

## Isolation modes

| Mode | Value | Use it for |
|---|---|---|
| In-process (default) | `"none"` | Your own bots, research, and anything where speed matters |
| Process | `"process"` | Bots you don't trust |

{class}`~maverick.enums.PlayerIsolation` holds both values.

## Configuration

The mode and the decision timeout can be set in three places. A setting is taken from
the first place that sets it:

1. **Arguments** of {class}`~maverick.game.Game`: `player_isolation` and
   `decision_timeout`.
2. **Environment variables**: `MAVERICK_PLAYER_ISOLATION` and
   `MAVERICK_DECISION_TIMEOUT`.
3. **`pyproject.toml`**: the `[tool.maverick]` table of the nearest `pyproject.toml`,
   searched from the current working directory upwards.

```toml
[tool.maverick]
player_isolation = "process"
decision_timeout = 5.0  # seconds
```

If none of them sets a value, players run in-process and there is no decision timeout.
Each setting is resolved on its own, so you can, for example, set the timeout in
`pyproject.toml` and switch the mode with the environment variable:

```bash
MAVERICK_PLAYER_ISOLATION=process python tournament.py
```

Invalid values raise a `ValueError` that names the source of the bad value. Unknown
keys in `[tool.maverick]` raise one as well, so typos don't go unnoticed. The resolved
settings of a game are available as `game.settings`.

## Decision timeout

`decision_timeout` limits how many seconds an isolated player may take for a single
decision. A player that exceeds it folds, and the game continues. When the late answer
arrives, it is discarded. The timeout only applies in process mode, because a function
running in the engine's own process can't be interrupted safely.

## Failures

An isolated player can't crash the game. The player folds, with a warning, if it:

- exceeds the decision timeout,
- raises an exception in `decide_action`,
- returns something that is not a valid `PlayerAction`, or
- its worker process dies. The player then folds every hand for the rest of the game.

Exceptions in event hooks are logged, as in in-process mode.

## Requirements and differences

- **Players must be picklable,** and their class must be importable in a fresh
  interpreter. Classes defined inside a function, in a notebook or in an interactive
  session can't be used. `add_player` raises a `TypeError` or `RuntimeError` for players
  that can't be sent to a worker.
- **Scripts must guard their entry point** with `if __name__ == "__main__":`. Workers
  are started with the `spawn` method, which imports the main module again in every
  worker.
- **Player state lives in the worker.** The worker gets a copy of the player when it is
  added. Attributes the bot changes while playing are not visible on the object you
  passed to `add_player`. `Player.game` on that object is still updated with the latest
  view. To get data out of a bot or into it, use `export_state` and `import_state`
  (see below).
- **Workers are started when players are added** and stopped when they leave, are
  eliminated, or the game ends. Use the game as a context manager, or call
  `game.close()`, to stop them early.
- **It's slower.** Every decision and every event hook crosses a process boundary, and
  starting a worker takes a fraction of a second. Hooks are sent without waiting for an
  answer, and only for the hooks a player implements.
- **`decision_time_seconds`** on recorded actions includes the time to communicate with
  the worker.

(player-state-export-import)=

## Player state: export and import

Listeners subscribed with `game.subscribe(...)` run in the engine's process and receive
the full `Game`, so game histories, transcripts and statistics collected by listeners
work the same in both modes. Data that a bot collects on itself is different, for
example the number of hands it has played, a model of its opponents, or the token usage
of an LLM it calls. In process mode that data lives in the worker's copy of the bot.

Players expose that data through a pair of optional hooks:

- {meth}`~maverick.player.Player.export_state` returns the player's state as a
  JSON-serializable `dict`. It should contain everything needed to restore the player
  later. Leave out secrets, such as API keys, and anything that can be recreated, such
  as clients.
- {meth}`~maverick.player.Player.import_state` restores a state returned by
  `export_state`.

The game calls them through {meth}`~maverick.game.Game.get_player_state` and
{meth}`~maverick.game.Game.set_player_state`:

```python
from maverick import Game, PlayerState
from maverick.players import CallBot


class CountingBot(CallBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.decisions = 0

    def decide_action(self, **kwargs):
        self.decisions += 1
        return super().decide_action(**kwargs)

    def export_state(self) -> dict:
        return {"decisions": self.decisions}

    def import_state(self, state: dict) -> None:
        self.decisions = state["decisions"]


if __name__ == "__main__":
    bot = CountingBot(name="Alice")
    with Game(small_blind=1, big_blind=2, player_isolation="process") as game:
        game.add_player(bot, state=PlayerState(stack=200))
        game.add_player(CallBot(name="Bob"), state=PlayerState(stack=200))
        game.start()

    saved = game.get_player_state(bot)
    print(saved)          # {'decisions': ...}
    print(bot.decisions)  # 0: this is the copy in your process

    # Continue counting in a new game
    with Game(small_blind=1, big_blind=2, player_isolation="process") as game:
        game.add_player(bot, state=PlayerState(stack=200))
        game.add_player(CallBot(name="Bob"), state=PlayerState(stack=200))
        game.set_player_state(bot, saved)
        game.start()
```

Both methods work the same in both isolation modes:

- **While the worker runs,** the engine asks it to export or import the state. You can
  call them between hands, for example from a listener, or before and after the game.
- **When the worker stops,** because the player left or was eliminated or the game
  ended, the worker exports the state one last time. `get_player_state` keeps returning
  that state afterwards. `set_player_state` raises a `RuntimeError`, because there is
  no worker left to restore it in.
- **In-process,** the bot's hooks are called directly.

Data always goes through JSON, in both directions and in both modes, so neither side
holds references into the other. Bots that don't implement `export_state` return
`None`.

If an isolated bot's `export_state` raises, times out, returns something that is not a
JSON-serializable `dict`, or its worker has died, `get_player_state` logs a warning and
returns `None`, so a misbehaving bot can't stop the code that collects results.
`set_player_state` raises a `RuntimeError` instead, because a state that silently fails
to load would be worse. In-process, exceptions from the hooks propagate.

## How the engine talks to workers

Every worker has its own pipe to the engine: `multiprocessing.Pipe`, a connected pair of
sockets. The two directions are treated differently on purpose:

| Direction | Format | Why |
|---|---|---|
| Engine → worker | Pickled Python objects | The engine is trusted, so the worker can safely unpickle what it receives. |
| Worker → engine | JSON, at most 1 MB per message | The worker runs untrusted code, so the engine must never unpickle anything it sends. |

Unpickling data can run arbitrary code. If the engine unpickled replies from workers, a
malicious bot could craft a reply that runs code in the engine's process, and from there
read the deck or change the game. That would undo the isolation. So decisions, hook
errors and exported states all come back as JSON, and the engine validates them, for
example actions with `PlayerAction.model_validate`.

The same reasoning rules out `multiprocessing.Queue` for replies from workers: a queue
unpickles every object taken out of it. A pipe lets the engine read raw bytes with
`recv_bytes`, with a size limit, and decode them as JSON itself.

## What process isolation doesn't cover

Process isolation keeps the engine's memory away from bots: they can't reach the
`Game`, the deck or hidden holdings, not even through interpreter introspection. It is
not a sandbox. A worker runs as the same operating system user as the engine, so a
malicious bot can still do anything that user can do:

- **Read the environment.** Workers inherit the environment variables of the engine's
  process, including API keys and other secrets of whoever runs the game. Remove
  secrets from the environment before starting a game with untrusted bots.
- **Use files and the network.** A bot can read any file the user can read, including
  files your own code writes during the game, and send data anywhere.
- **Read saved games.** If the game is saved with `save_dir`, a bot can read the
  checkpoint of the last hand, which predicts the cards of the next one (see
  {doc}`saving_games`). Save games with untrusted bots to a directory the workers
  can't read.
- **Interfere with other processes,** for example by killing the engine or the workers
  of other players, which stops the game.

To run bots you don't trust at all, also run the game in a container or as a separate
operating system user with no access to secrets, files or the network it doesn't need.

Beyond that, process isolation doesn't cover:

- **Code that runs when the bot is created.** You import the bot's module and create
  the player in your own process, so code at import time or in `__init__` runs next to
  the engine. If you don't trust that code either, create players in a separate process
  or container.
- **Resource limits.** A worker can use as much CPU and memory as the operating system
  allows. Use containers or operating system limits if you need hard limits.
- **Random numbers in bots.** Workers don't inherit the random state of your script,
  so seeding `random` doesn't make the decisions of isolated bots reproducible. The
  cards are not affected: the game shuffles with its own generator, which you can seed
  with `Game(seed=...)` (see {doc}`reproducibility`).
