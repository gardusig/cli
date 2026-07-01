---
name: read-docs-reference
description: >-
  Read-only: legacy monolithic docs/REFERENCE.md + docs/reference/wiki templates (migration). Primary narrative
  is docs/README.md + optional docs/ mirror per read-repo-layout. Callers: @git-docs. Does not write files.
---
# Internal: Reference documentation template (`read-docs-reference`)

**Read-only library.** **Current** default narrative: **`docs/README.md`** + optional **`docs/`** mirror (**[`read-repo-layout`](../repo-layout/SKILL.md)**). **Other** repos may add a **profile** wiki per **`read-docs-wiki`**—**cursor-skills** does not ship **`docs/wiki/`**. This skill supplies **extra** **migration / legacy** tracks when a repo still wants **`docs/reference/**`** or **`docs/REFERENCE.md`**:

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- For **wiki layout**, copy from **`docs/`** (this pack) or your repo’s existing **`docs/`** first, then split catalogs into **`docs/reference/*.md`** when **`wiki-reference-scaffold/SKILL.md`** would exceed **`@git-docs`** size limits.
- For **legacy** repos, copy **`wiki-reference-scaffold/SKILL.md`** into **`docs/REFERENCE.md`**; replace placeholder rows with real skills.
- Keep **public** skills **before** **internal** in any catalog tables.
- Use consistent table columns (**Invoke** | **Source** | **Description**) or document your variant once per repo.

## Do not

- Run commands or edit the filesystem from this skill.

---

## Rendered paths

| Layout | Paths |
| --- | --- |
| **Profile wiki** (preferred) | Often **`docs/README.md`** alone (**minimal**); or expanded sections per **`read-docs-wiki`** when you need deeper hubs |
| **Optional skills mirror** | **`docs/.../README.md`** (full tree when opted in) |
| Minimal root | **`README.md`** at repo root |
| Legacy wiki | **`docs/README.md`**, **`docs/reference/**`** |
| Legacy monolith | **`docs/REFERENCE.md`** |
| Flat variant | **`REFERENCE.md`** at repo root |

---

## See also

- [`read-docs-wiki`](../doc-wiki/SKILL.md) — doc depth orientation
- [`read-repo-layout`](../repo-layout/SKILL.md) — hub contract
- [`read-docs-exemplars`](../doc-exemplars/SKILL.md) — markdown patterns + rubric
- [`read-docs-graphs`](../doc-graphs/SKILL.md) — diagram authoring (not required **`GRAPHS.md`**)
- [`read-docs-user-guide`](../doc-user-guide/SKILL.md) — **`USER_GUIDE.md`**
- [`read-docs-readme-root`](../readme-root/SKILL.md) — root **`README.md`**
