---
name: maverick
description: Answer questions about the Maverick poker library by consulting the locally built documentation. Auto-invoked when the user asks anything about Maverick's API, features, concepts, or usage.
allowed-tools: Read, Glob
---

You are answering a question about the Maverick poker library.

## Step 1 – Check for built documentation

Check whether `docs/build/html/llms.txt` exists.

- If it does **not** exist, stop and tell the user:
  > The local documentation hasn't been built yet. Please run `uv run sphinx-build docs/source docs/build/html` and then ask again.

## Step 2 – Read the page index

Read `docs/build/html/llms.txt`. It contains:
- A project overview at the top
- A `## Pages` section listing every documentation page in the format:
  `- [Page Title](relative/path.html.md): short summary`

The paths are relative to `docs/build/html/`.

## Step 3 – Select relevant pages

Based on the user's question and the summaries in `llms.txt`, identify the most relevant pages. Prefer:
- Specific API reference pages (`_autosummary/`) for questions about a class or function
- User guide pages (`user_guide/`) for conceptual or usage questions
- Example pages (`examples/`) for how-to questions

Read only the pages that are clearly relevant — do not read everything.

## Step 4 – Read selected pages and answer

Read the selected pages from `docs/build/html/<relative-path>` and answer the user's question based on their content. Cite the page titles you consulted.
