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
| --- | --- | --- |
| **maverick** | "write a bot", "set up a game", "run untrusted bots", "save and resume a game", "replay a game" | Teaches the library's core usage: the player contract, betting semantics, game setup and seeding, events, listeners, game histories, player isolation, player state export/import, and saving, replaying and resuming games |
| **maverick-docs** | "how do I use Maverick", "what does X do in Maverick", "show me an example of…" | Reads the online documentation index, selects relevant pages, and answers from their content |
