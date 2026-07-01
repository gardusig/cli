---
name: read-docs-readme-tree
description: >-
  Read-only: optional docs/ mirror parity checklist and greenfield hints vs skills/. No tree regen or bulk README apply
  from pack skills—use write-quality-documentation for in-place edits. Does not write files.
---
# Internal: Docs mirror notes (`read-docs-readme-tree`)

**Read-only.** This pack keeps **`docs/**`** as a **human-facing mirror** of **`skills/`** when you choose that layout. **Agents** do **not** run a separate “mirror regen” step after verify. **`write-quality-documentation`** edits **existing** markdown **in place**; if a **`docs/.../README.md`** is missing, add it in a normal edit (same PR) using the bootstrap bullets below.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Bootstrap (greenfield or new folders)

1. **Domain layout** — **[`read-repo-layout`](../repo-layout/SKILL.md)** — public skills under **`skills/<domain>/<verb>/`**; shared libraries under **`skills/internal/read/<domain>/**`** vs **`skills/internal/write/<domain>/**`** depending on whether they mutate the machine or GitHub.
2. **Mirror hub pages** — **`docs/<same-relpath>/README.md`**: short overview, **`## Contents`** as **numbered lists** only (**[`read-docs-index`](../doc-index/SKILL.md)**), overview prose per **[`read-docs-explanation`](../doc-explanation/SKILL.md)**.
3. **Diagrams** — Add fenced **`mermaid`** only when a diagram clarifies flow; palette and hierarchy per **[`read-docs-graphs`](../doc-graphs/SKILL.md)**. Example scaffolds live in **`skills/internal/read/workflow/doc-graphs/diagrams/*/SKILL.md`** (optional references, not required files in consuming repos).
4. **Tables** — Data tables in reference sections: sort rows, call out large rows (**[`read-docs-table`](../doc-table/SKILL.md)**). Never use a markdown **table** for a pure index (**[`read-docs-index`](../doc-index/SKILL.md)**).

## Optional parity checklist (human)

If this repo uses a **`docs/`** mirror: skip **`.gitignore`**d paths; spot-check that important **`skills/.../`** dirs have a sibling **`docs/.../README.md`** when that is your convention; **`## Contents`** ordered lexicographically; relative links into **`skills/`** still resolve.

## Do not

- Treat this skill as part of the post-verify doc polish path—the verify pipeline ends at **`write-quality-documentation`**.

## See also

- [`read-repo-layout`](../repo-layout/SKILL.md)
- [`read-docs-mirror-bootstrap`](../docs-mirror-bootstrap/SKILL.md)
- [`write-quality-documentation`](../../../internal/write/quality/documentation/SKILL.md)
- [`read-docs-readme-root`](../readme-root/SKILL.md)
