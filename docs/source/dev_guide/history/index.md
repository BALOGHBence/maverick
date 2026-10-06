---
myst:
  html_meta:
    description: "Detailed, per-change development history of Maverick: one entry per pull request, each with a summary followed by the details."
---

# Development History

The development history records every change to the codebase in detail, one entry per
pull request. It complements two other documents:

| Document | What it records | Edited over time? |
|---|---|---|
| `CHANGELOG.md` | What users need to know, per release, at a high level | Until the release |
| {doc}`../design_decisions` | Why the code is the way it is *now* | Yes, kept up to date |
| Development history | What changed in each pull request, why and how | No, written once |

Entries are a historical record: once merged, they are not updated to reflect later
changes. If a later change revisits a decision, its own entry says so and links back.

These pages are deliberately excluded from `llms.txt` and `llms-full.txt` (see
{doc}`../llm_friendly_docs`): they describe how the code got here, not how to use it.

## Conventions

- **One entry per pull request**, written in the feature branch as part of the PR, so it
  is reviewed together with the code.
- **File name:** `YYYY-MM-DD-short-slug.md` in `docs/source/dev_guide/history/`, using
  the date the entry is written. Dates sort chronologically and, unlike sequence
  numbers, don't collide between branches developed in parallel.
- **Summary first:** the summary must be readable on its own. The details sections are
  optional; leave out the ones that don't apply.
- **Link, don't repeat:** refer to {doc}`../design_decisions`, issues and pull requests
  instead of copying their content.
- New entries appear in the list below automatically, newest first.

## Template

```markdown
---
myst:
  html_meta:
    description: "One-line summary of the change."
---

# <Title of the change>

| | |
|---|---|
| **Date** | YYYY-MM-DD |
| **PR / Issues** | #… |
| **Version** | x.y.z |
| **Breaking** | Yes / No |

## Summary

Three to six sentences: what changed, why, and what the outcome is.

## Details

### Motivation

### Changes

### Breaking changes and migration

### Design decisions and alternatives considered

### Performance

### Testing

### Follow-ups and known limitations
```

## Entries

```{toctree}
:glob:
:reversed:
:maxdepth: 1

*
```
