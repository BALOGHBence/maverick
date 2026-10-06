---
name: maverick-docs
description: Answer questions about the Maverick poker library by consulting the online documentation at https://pymaverick.readthedocs.io/en/latest/. Auto-invoked when the user asks anything about Maverick's API, features, concepts, or usage.
allowed-tools: WebFetch
---

You are answering a question about the Maverick poker library.

The documentation is hosted at the base URL `https://pymaverick.readthedocs.io/en/latest/`.

## Step 1 – Read the page index

Fetch `https://pymaverick.readthedocs.io/en/latest/llms.txt`. It contains:
- A project overview at the top
- A `## Pages` section listing every documentation page in the format:
  `- [Page Title](relative/path.html.md): short summary`

If the index cannot be fetched, stop and tell the user that the online documentation is currently unreachable.

## Step 2 – Resolve links

Every link in `llms.txt` is a **relative URL**, resolved against the directory that contains the `llms.txt` file being read. Each link points to a Markdown version of a documentation page (`.html.md`), which contains the full page content.

Examples for the top-level index at `https://pymaverick.readthedocs.io/en/latest/llms.txt`:

- `[Overview](overview.html.md)` → `https://pymaverick.readthedocs.io/en/latest/overview.html.md`
- `[User Guide](user_guide/index.html.md)` → `https://pymaverick.readthedocs.io/en/latest/user_guide/index.html.md`
- `[Configuring and Running Games](user_guide/games.html.md)` → `https://pymaverick.readthedocs.io/en/latest/user_guide/games.html.md`
- `[maverick.game.Game](_autosummary/maverick.game.Game.html.md)` → `https://pymaverick.readthedocs.io/en/latest/_autosummary/maverick.game.Game.html.md`

Each subdirectory also has its own index (for example `https://pymaverick.readthedocs.io/en/latest/user_guide/llms.txt`) whose links are relative to **that subdirectory**, so the same page is linked there as `games.html.md` and still resolves to `https://pymaverick.readthedocs.io/en/latest/user_guide/games.html.md`.

## Step 3 – Select relevant pages

Based on the user's question and the summaries in `llms.txt`, identify the most relevant pages. Prefer:
- Specific API reference pages (`_autosummary/`) for questions about a class or function
- User guide pages (`user_guide/`) for conceptual or usage questions
- Example pages (`examples/`) for how-to questions

Fetch only the pages that are clearly relevant — do not fetch everything.

## Step 4 – Read selected pages and answer

Fetch the selected `.html.md` pages using the resolved absolute URLs and answer the user's question based on their content. Cite the page titles and URLs you consulted.
