<div align="center">
  <p>
    <a href="https://readthedocs.org/projects/pymaverick/badge/?version=latest)](https://pymaverick.readthedocs.io/en/latest/?badge=latest" target="_blank">
      <img width="100%" src="https://github.com/BALOGHBence/maverick/blob/main/cover_image.png?raw=true" alt="Maverick banner"></a>
  </p>

  <div>
    <a href="https://pymaverick.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/pymaverick/badge/?version=latest" alt="Documentation Status"></a>
    <a href="https://codecov.io/gh/BALOGHBence/maverick"><img src="https://codecov.io/gh/BALOGHBence/maverick/graph/badge.svg?token=VDRFOUJYUG" alt="Code Coverage"></a>
    <a href="https://app.codacy.com/gh/BALOGHBence/maverick/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/c960167518b646eea31cf1ff02a13823" alt="Code Quality"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
  </div>

  <br>

  <div>
    <a href="https://pymaverick.readthedocs.io/en/latest/index.html"><img src="https://img.shields.io/badge/Documentation-blue?style=flat" alt="Documentation"></a>
  </div>
  
  <br>

  <div>
    <a href="https://buymeacoffee.com/benceeokf"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="BuyMeACoffee"></a>
  </div>

  <br>

  <p>
    A Python library for simulating poker games with custom player strategies.
  </p>

</div>

Poker is a great sandbox for decision-making systems: hidden information, imperfect opponents, probabilistic outcomes, and lots of room for experimentation.

**Maverick** is a Python library for simulating poker games with custom player strategies. It gives you a complete poker game loop (dealing, betting rounds, showdown, pot distribution) plus a clean player interface so you can swap strategies in and out.

## Highlights

Maverick is designed for building and testing strategies:

- **Composable API**: build your own players by implementing a single method.
- **State-machine engine**: clear phases and transitions, easier to reason about.
- **Event stream**: observe what happens (for logging, analytics, replay, debugging).
- **Hand evaluation utilities**: score hands and compare outcomes.

If you’ve ever wanted to:

- benchmark bots against each other,
- run repeatable simulations,
- prototype an agent that makes betting decisions,

…Maverick is meant to make that workflow straightforward.

## Installation

You can install Maverick from PyPI

```bash
pip install maverick
```

## Your first game (minimal example)

Here’s an end-to-end example using built-in bots:

```python
from maverick import Game, PlayerLike, PlayerState
from maverick.players import FoldBot, CallBot, AggressiveBot

# Create a game with blinds and a stop condition
game = Game(small_blind=10, big_blind=20, max_hands=10)

# Create players
players: list[PlayerLike] = [
    CallBot(name="CallBot", state=PlayerState(stack=1000)),
    AggressiveBot(name="AggroBot", state=PlayerState(stack=1000)),
    FoldBot(name="FoldBot", state=PlayerState(stack=1000)),
]

for player in players:
    game.add_player(player)

game.start()

# Inspect results
for player in players:
    print(f"{player.name} - Stack: {player.state.stack}")
```

(See the documentation for more examples and APIs.)

## Documentation

The project has extensive [documentation](https://pymaverick.readthedocs.io/en/latest/index.html) hosted on ReadTheDocs. Most library information is documented there, with only the essentials kept here.

## Changes and Versioning

The changelog is maintained in [CHANGELOG.md](CHANGELOG.md).
The project adheres to [semantic versioning](https://semver.org/).

## Contributing

Contributions are currently expected in any the following ways:

- **finding bugs**
  If you run into trouble when using the library and you think it is a bug, feel free to raise an issue.
- **feedback**
  All kinds of ideas are welcome. For instance if you feel like something is still shady (after reading the user guide), we want to know. Be gentle though, the development of the library is financially not supported yet.
- **feature requests**
  Tell us what you think is missing (with realistic expectations).
- **examples**
  If you've done something with the library and you think that it would make for a good example, get in touch with the developers and we will happily inlude it in the documention.
- **funding**
  Use one of the supported funding channels. Any amount you can afford is appreciated.
- **sharing is caring**
  If you like the library, share it with your friends or colleagues so they can like it too.

In all cases, read the [contributing guidelines](CONTRIBUTING.md) before you do anything.

## License

This package is licensed under the [MIT license](LICENSE.txt).
