---
name: read-docs-explanation
description: >-
  Read-only: how to write overview/explanation sections for docs mirror pages from SKILL.md. Callers: @git-docs,
  write-quality-documentation. Does not write files.
---
# Internal: Doc explanation rules (`read-docs-explanation`)

**Read-only library.** **Normative guidance** for **Overview** / narrative blocks on **`docs/<domain>/.../README.md`** or optional **`docs/.../README.md`** mirror pages.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Rules

1. Derive **what / when / boundaries** from **`SKILL.md`** frontmatter **`description`** and **Do** / **Do not** sections.
2. **Link** delegates (**`read-*` / `write-*`**, sibling public skills) with **one line why**.
3. Avoid speculative roadmaps—describe **current** behavior.

## See also

- [`read-docs-index`](../doc-index/SKILL.md)
- [`read-docs-graphs`](../doc-graphs/SKILL.md) — when to add **mermaid** + palette
- [`read-docs-index`](../doc-index/SKILL.md) — pair narrative sections with stable page navigation.
