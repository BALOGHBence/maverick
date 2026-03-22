# LLM-Friendly Documentation

Maverick's documentation is built to be consumed not just by humans in a browser, but also by LLMs. Every page in the HTML docs has a corresponding Markdown version that can be fed directly into an AI assistant's context window.

## Why

LLMs work best with clean, structured text — not HTML. When a developer wants to ask Claude or ChatGPT questions about Maverick, they should be able to point the model at the documentation without any scraping or conversion step in between.

The [llms.txt standard](https://llmstxt.org/) formalises this idea: documentation sites publish a `llms.txt` index and per-page Markdown files alongside the normal HTML output, making the documentation machine-readable by convention.

## The `sphinx-llm` Extension

The [`sphinx-llm`](https://github.com/NVIDIA/sphinx-llm) extension (configured via `"sphinx_llm.txt"` in `docs/source/conf.py`) hooks into the Sphinx build and generates the following files in `docs/build/html/`:

| File | Description |
|---|---|
| `llms.txt` | Index listing every page with its title and a one-sentence description |
| `llms-full.txt` | The entire documentation concatenated into a single Markdown file |
| `{pagename}.html.md` | Per-page Markdown, one file per HTML page |

The per-page files follow a deterministic naming convention: the HTML file and its Markdown counterpart live in the same directory with the same base name.

```
docs/build/html/
├── api_reference.html
├── api_reference.html.md          ← markdown twin
├── _autosummary/
│   ├── maverick.game.Game.html
│   └── maverick.game.Game.html.md ← markdown twin
└── ...
```

The extension works by spawning a secondary Sphinx build using the `markdown` builder, then renaming the output files to the `.html.md` convention and copying them into the HTML output directory.

### Configuration

The extension is enabled in `docs/source/conf.py` and requires no additional settings beyond being listed in `extensions`:

```python
extensions = [
    ...
    "sphinx_llm.txt",
]
```

The `sphinx-llm[gen]` package is listed in the `docs` dependency group in `pyproject.toml`.

## The Per-Page Download Button

Knowing that per-page Markdown files exist is one thing; making them discoverable to a human browsing the docs is another. The sphinx-book-theme already renders a download dropdown in the article header with options for the source file (`.rst`) and a print-to-PDF button. We add a `.md` entry to that same dropdown so that any page can be downloaded as Markdown in one click.

### How it works

A small JavaScript file (`docs/source/_static/js/download_md.js`) runs on every page. It:

1. Reads `window.location.pathname` to determine the current page URL.
2. Derives the Markdown file URL — for the standard HTML builder this is a simple substitution (`api_reference.html` → `api_reference.html.md`); for the dirhtml builder used by ReadTheDocs (where URLs end in `/`) it appends `index.html.md`.
3. Constructs a `<li>` element styled identically to the existing download items.
4. Prepends it to the `.dropdown-download-buttons .dropdown-menu` element that the theme already renders.

The script is loaded globally via `html_js_files` in `conf.py`:

```python
html_js_files = ["js/download_md.js"]
```

The DOM target (`.dropdown-download-buttons`) is specific enough to be stable across theme updates, but the script is also defensive: if the element is not found on a given page, it exits silently without throwing an error.

### Why JavaScript instead of a Jinja2 template override

Sphinx-book-theme inherits its template structure from pydata-sphinx-theme, and the article header button area is generated through several layers of macro calls. Overriding a template at the right level would require coupling the implementation to internal theme internals that are not part of the public API and tend to change between minor releases. The JavaScript approach queries a stable, semantic CSS class that represents the download button group, making it resilient to theme updates.

## The Claude Code Plugin

Maverick ships a Claude Code plugin at `maverick-plugin/` that users can install via:

```text
/plugin marketplace add BALOGHBence/maverick
```

The plugin follows the [claude-skills-marketplace](https://github.com/mhattingpete/claude-skills-marketplace) format and is registered in `.claude-plugin/marketplace.json`. Skills are auto-discovered from `maverick-plugin/skills/`.

### The symlink in `.claude/skills/`

`.claude/skills/maverick/SKILL.md` is a symlink pointing to `maverick-plugin/skills/api-consulting.md`. This keeps the project-local Claude Code skill in sync with the canonical skill file in the plugin without duplication.

**Windows caveat:** git on Windows does not create symlinks by default. Without symlink support, this file is checked out as a plain text file containing the path string, and the project-local skill will not work. To fix this, enable **Developer Mode** in Windows Settings or run the following before cloning:

```bash
git config --global core.symlinks true
```

Users of the plugin installed via `/plugin marketplace add` are not affected by this — the marketplace installs skills to `~/.claude/skills/` directly and does not involve the symlink.
