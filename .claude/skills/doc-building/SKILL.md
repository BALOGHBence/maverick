---
name: doc-building
description: This skill should be used when the user asks to "build the docs", "rebuild documentation", "generate sphinx docs", "compile the documentation", "build html docs", or mentions rebuilding/updating the Maverick documentation.
---

# Doc Building

Builds the Sphinx documentation for the Maverick project using a dedicated script.

## When This Skill Applies

Activate when the user wants to build or rebuild the project documentation.

## How to Build

Run the build script, optionally passing a Sphinx target (default: `html`):

```sh
bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh [TARGET]
```

**Examples:**
```sh
# Build HTML docs (default)
bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh

# Build a specific target
bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh dirhtml
bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh latex
```

## Output

Built files are placed under `docs/build/<TARGET>/`. For the default HTML build, the output is at `docs/build/html/`.

## On Build Failure

If the build fails:
1. Check the error output for the file and line causing the issue.
2. Fix the source file in `docs/source/`.
3. Re-run the script.
