---
name: read-docs-wiki
description: >-
  Read-only: light orientation for how deep docs/ can go on other repositories; this pack uses docs/README.md + docs/
  mirror only. No structural scaffold workflow in pack skills. Does not write files.
---
# Internal: Doc depth orientation (`read-docs-wiki`)

**Read-only.** **This repository** (**cursor-skills**): documentation is **`docs/README.md`** (hub) + **`docs/`** mirroring **`skills/`**. There is **no** separate **`docs/wiki/`** profile tree checked in here.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Bootstrap hints (when starting from scratch)

1. **Pick hub depth** — Smallest useful surface is **`docs/README.md`** + links; add domain wikis (**`docs/git.md`**, **`docs/gh.md`**, …) when **`@`** skills multiply.
2. **Keep domains aligned** — Mirror **`skills/`** folder names under **`docs/`** when you want a wiki beside the pack (**`read-repo-layout`**).
3. **API / schema docs** — Add **`docs/api/`** (or similar) only when the repo actually ships HTTP/GraphQL/proto contracts worth documenting (**`read-dependencies-discover`** can hint at signals).
4. **Shape** — Indexes, tables, diagrams: **`read-docs-index`**, **`read-docs-table`**, **`read-docs-graphs`**, **`read-docs-explanation`**.
5. **Hub starter** — For a cursor-skills-style docs hub scaffold, start from **`read-docs-reference/docs-hub-scaffold/SKILL.md`**.

## Do not

- Run commands or write files from this skill.
- Treat this file as a mandatory multi-folder **`docs/wiki/`** scaffold for every consumer of the pack.

## See also

- [`read-repo-classification`](../repo-classification/SKILL.md)
- [`read-repo-layout`](../repo-layout/SKILL.md)
- [`read-docs-readme-tree`](../readme-tree/SKILL.md)
- [`docs/README.md`](../../../../docs/README.md)
