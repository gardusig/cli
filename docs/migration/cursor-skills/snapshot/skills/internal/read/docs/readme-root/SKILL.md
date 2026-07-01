---
name: read-docs-readme-root
description: >-
  Read-only: minimal repository root README.md (link docs hub); optional Appendix D CI. Full narrative lives in
  docs/ for this pack. Callers: @git-docs, write-quality-documentation. Does not write files.
---
# Internal: Root README template (`read-docs-readme-root`)

**Read-only library.** **This pack (cursor-skills):** root **`README.md`** stays **short**—opening **Quick guide** (what/why + a few usage examples), **`./.cursor/scripts/install.sh`** (flags + env), link **[`docs/README.md`](../../../../docs/README.md)**, short **Documentation** pointer, optional **Usage flow** Mermaid—no full skill catalog in root. **Legacy / other repos:** full **superset** scaffold lives in **[`./root-readme-scaffold/SKILL.md`](./root-readme-scaffold/SKILL.md)** and **Appendix A** below.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- **Default (this pack):** Root = **short** entry: optional opening **Quick guide** (what/why + brief examples), **`./.cursor/scripts/install.sh`** (install + verify flags), **link [`docs/README.md`](../../../../docs/README.md)**; optional link **[`docs/README.md`](../../../../docs/README.md)**; optional **Usage flow** diagram (**`read-docs-graphs`**).
- Prefer the **brief pack variant** in **[`./root-readme-scaffold/SKILL.md`](./root-readme-scaffold/SKILL.md)**: emoji on top-level `##` headings, one compact comparison table when useful, and at most 0-2 Mermaid blocks in root.
- **Legacy / monolithic root:** Use **Appendix A** + **[`./root-readme-scaffold/SKILL.md`](./root-readme-scaffold/SKILL.md)** (Quick guide, mermaid, Contents, …).
- Keep install **minimal**; **prompt** the user to run **Terminal batches** for heavy setup (**public `gh-*`** execution contract).
- Optional **Appendix D** (CI/coverage) when real signals exist.

## Do not

- Put full per-skill catalogs in root—use **`docs/git.md`**, **`docs/gh.md`**, **`docs/read.md`**, **`docs/write.md`**, … (**this** pack) or optional **`docs/`** mirror elsewhere.
- **Stuff** long reference into root when **`docs/README.md`** can own it.

---

## Appendix A — Template: main (root) README

**Full scaffold:** **[`./root-readme-scaffold/SKILL.md`](./root-readme-scaffold/SKILL.md)**.

Use for **repository root** `README.md`. Replace placeholders.

**Principles** (full root README — legacy or non-mirror repos)

- **Docs mirror pack:** prefer **minimal** root + **`docs/`** hub per **`read-repo-layout`** §2.
- **Subtree scope:** Summarize at high level; **do not** paste full inventories—**[`docs/README.md`](../../../../docs/README.md)** and **`docs/<domain>/README.md`** files own domain indexes (**this** pack).
- **`## Contents` (root):** **numbered nested lists** only—**no markdown table** for the index.
- **Tables:** OK in **reference** sections—not for directory listings.
- **Section titles:** keep emoji on major `##` headings for scanability in pack-facing docs.
- **Mermaid:** at least one **colored** diagram when the root is long-form (**`read-docs-graphs`** + **`skills/internal/read/workflow/doc-graphs/diagrams/*/SKILL.md`** scaffolds; human index **`docs/README.md`**).
- **Estimates:** optional **`## Estimates` / `## Economics`** for service-level roll-ups (**explicitly labeled estimates**).
- **No forecasted features**—describe **current** behavior only.

**Conventions:** **Timelines**: **newest → oldest**. **Data tables**: sort rows **lexicographically** on the first column; **call out largest** rows (**`read-docs-table`**).

---

## Appendix D — Optional: coverage and CI quick block (root only)

Use when the repo has **real** signals (not placeholder). Omit the whole section if unknown.

```markdown
## Health

- **CI:** [![CI](<badge-url>)](<actions-or-ci-url>) — <what it runs>
- **Coverage:** <e.g. `npm run test -- --coverage` or link to report> — <threshold or “see CI”>
```

---

## Exemplar (this repository)

Live root **[`README.md`](../../../../README.md)** is **source of truth**: it stays brief, uses emoji on major `##` headings, includes a compact lane-comparison table, and keeps Mermaid focused on lane/flow visuals. Merge Appendix A only when the repo truly needs long-form root documentation.

---

## See also

- [`read-docs-readme-tree`](../readme-tree/SKILL.md) — optional **`docs/`** mirror checklist + bootstrap
- [`read-docs-user-guide`](../doc-user-guide/SKILL.md)
- [`read-docs-reference`](../doc-reference/SKILL.md)
