---
name: read-docs-index
description: >-
  Read-only: rules for doc page indexes (numbered lists, lexicographic order, no tables in Contents). Callers:
  @git-docs, write-quality-documentation. Does not write files.
---
# Internal: Doc index rules (`read-docs-index`)

**Read-only library.** **Normative rules** for **navigation** sections on **`docs/**`** pages.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Rules

1. **`## Contents`** (and **See also** when it is pure navigation): **numbered nested lists** only.
2. **Lexicographic** ordering of children (stable convention per repo).
3. **No markdown tables** for directory listings—GitHub file view is already tabular.
4. Link to **source** **`SKILL.md`** where the doc mirrors a skill folder.

## Do not

- Duplicate full skeleton bodies here—reuse this file's rules and sibling doc libraries instead.

## See also

- [`read-docs-explanation`](../doc-explanation/SKILL.md)
- [`read-repo-layout`](../repo-layout/SKILL.md)
- [`docs/README.md`](../../../../docs/README.md)
