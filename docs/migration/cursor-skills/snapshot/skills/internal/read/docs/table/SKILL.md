---
name: read-docs-table
description: >-
  Read-only: markdown table conventions for doc reference sections (not indexes). Callers: @git-docs,
  write-quality-documentation. Does not write files.
---
# Internal: Doc table rules (`read-docs-table`)

**Read-only library.** **When** to use **markdown tables** on **`docs/`** pages: **reference** and **comparison** sections only—not **`## Contents`**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Rules

1. **Sort** rows by **first column** lexicographically.
2. After the table, **call out** the **largest** row by the chosen metric and **why** it matters.
3. Optional **summary** prose for aggregates—avoid double-counting with child pages.

## See also

- [`read-docs-index`](../doc-index/SKILL.md)
- [`read-docs-explanation`](../doc-explanation/SKILL.md)
