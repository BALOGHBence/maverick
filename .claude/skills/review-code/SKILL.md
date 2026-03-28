---
name: review-code
description: Review code changes in the Maverick repository for correctness, style, and adherence to project conventions. Triggered when the user asks to review code, check a diff, or audit recent changes.
allowed-tools: Read, Glob, Grep, Bash
---

# Code Review

Review code changes in the Maverick repository for bugs, style issues, and adherence to project conventions.

## Step 1 – Determine scope

If the user specifies a file, path, or commit/PR, use that as the scope. Otherwise default to uncommitted changes:

```bash
# Staged + unstaged changes
git diff HEAD
```

If there are no uncommitted changes, fall back to the last commit:

```bash
git diff HEAD~1 HEAD
```

Read any changed source files in full when context from the diff alone is insufficient to judge correctness.

## Step 2 – Review checklist

Go through every changed file and evaluate the items below. Only flag items that are **actually violated** — do not invent issues.

### Types & interfaces
- [ ] All functions and methods have type hints.
- [ ] `decide_action` signature matches the required keyword-only interface exactly.

### Style (PEP 8 + project conventions)
- [ ] Line length ≤ 88 characters (Black-compatible).
- [ ] No unused imports or variables.
- [ ] No bare `except:` clauses.
- [ ] Enums from `enums.py` are used instead of raw strings/ints for street names, action types, event types, etc.
- [ ] No namespace pollution — imports are from the correct modules and do not introduce unnecessary names into the global scope. 
- [ ] No wildcard imports (e.g. `from module import *`).
- [ ] Numpy style docstrings are present for all public classes and functions.

### Tests
- [ ] New public functions or non-trivial behaviour have corresponding tests in `tests/`.
- [ ] Tests do not mock internal game state — they exercise the real `Game` object.

### Docs / changelog
- [ ] Public API additions/changes are reflected in the relevant docstring.
- [ ] `CHANGELOG.md` is updated if the change is user-visible.
- [ ] If the change affects how users should build or run the docs, `docs/` is updated accordingly.
- [ ] Examples in `docs/source/examples/` are updated if relevant.
- [ ] If new classes or functions are added, they are included in the API reference docs.

## Step 3 – Report

Structure your report as follows:

### Summary
One-paragraph overview of what changed and overall quality.

### Issues
List each finding as:

**[SEVERITY] File:line — short title**
> Explanation of the problem and suggested fix.

Severity levels: `BUG` (incorrect behaviour), `WARN` (potential issue or smell), `STYLE` (convention/formatting).

If there are no issues, say so explicitly.

### Suggestions *(optional)*
Non-blocking ideas for improvement — only include if genuinely valuable.
