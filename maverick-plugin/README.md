# Maverick Claude Code Plugin

Claude Code skills for working with the [Maverick](https://github.com/BALOGHBence/maverick) poker library.

## Installation

```
/plugin marketplace add BALOGHBence/maverick
```

Or install this plugin individually:

```
/plugin marketplace add BALOGHBence/maverick/maverick-plugin
```

## Skills

Skills activate automatically based on natural language — no slash commands needed.

| Skill | Activates when you say… | What it does |
|---|---|---|
| **api-consulting** | "how do I use Maverick", "what does X do in Maverick", "show me an example of…" | Reads the locally built documentation index, selects relevant pages, and answers from their content |
| **bot-generating** | "create a bot", "write a player", "implement a strategy", "scaffold a decide_action" | Guides you through requirements and generates a complete `Player` subclass |
| **scenario-building** | "set up a game", "create a scenario", "test hand", "reproduce a bug", "Omaha setup" | Produces a self-contained game setup script with optional event subscriptions and test assertions |

## Notes

- **api-consulting** requires locally built documentation. If it isn't built yet, the skill will prompt you to run:
  ```bash
  uv run sphinx-build docs/source docs/build/html
  ```
- **bot-generating** and **scenario-building** work without built docs.
