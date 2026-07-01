---
name: read-docs-user-guide
description: >-
  Read-only: TEMPLATE.md for legacy docs/USER_GUIDE.md (migration). README-only repos fold narrative into
  read-docs-readme-root / root README. Callers: @git-docs. Does
  not write files.
---
# Internal: User guide template (`read-docs-user-guide`)

**Read-only library.** Canonical **body** for **legacy** **`docs/USER_GUIDE.md`** when a repo still uses a **`docs/`** hub. **Default** for this pack: fold the same material into **root `README.md`** (**[`read-docs-readme-root`](../readme-root/SKILL.md)**). Full source: **`[TEMPLATE.md](./TEMPLATE.md)`**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- **Install from scratch** (especially **macOS** **Terminal**, **raw** `brew` / `git` / `gh` commands).
- Describe **happy path** workflows (e.g. **`gh-start` → work → `gh-pr`**).
- Point **short** install blurbs at root **`README.md`**; keep **catalogs** under **`docs/*.md`** hubs (**this** pack: **`docs/git.md`**, **`docs/gh.md`**, **`docs/read.md`**, **`docs/write.md`**) or optional wiki-only layouts on other repos, or, in legacy repos, **`docs/reference/**`** / **`REFERENCE.md`**.
- Document **`.cursor/`** or project-local artifact dirs with a **who writes what** table.

## Do not

- Duplicate long wiki tables — link **`docs/README.md`** (**this** pack), optional **`docs/README.md`**, or **`docs/reference/**`** (legacy).

---

## Rendered path

| Layout | Path |
| --- | --- |
| **Domain docs** (**this** pack) | **`docs/README.md`** + **`docs/git.md`** / **`docs/gh.md`** / **`docs/read.md`** / **`docs/write.md`** — **[`read-repo-layout`](../repo-layout/SKILL.md)** |
| Legacy hub | **`docs/USER_GUIDE.md`** |
| Variant | **`USER_GUIDE.md`** at repo root |

---

## See also

- [`read-docs-exemplars`](../doc-exemplars/SKILL.md) — public markdown patterns + rubric
- [`read-docs-reference`](../doc-reference/SKILL.md)
- [`read-docs-graphs`](../doc-graphs/SKILL.md)
- [`read-docs-wiki`](../doc-wiki/SKILL.md) — doc depth orientation
- [`@git-docs`](../../../git/docs/SKILL.md)
