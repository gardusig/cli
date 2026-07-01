---
name: read-repo-discovery
description: >-
  Read-only: repo discovery loop contract — pendencies, desirables checklist, standards baseline, refinement turns,
  and issue-candidate bundles with execution pointers. Consumed by chat/planning and @gh-issue; no git or GitHub mutations.
---
# Internal: GitHub discovery loop (`read-repo-discovery`)

**Read-only library.** Normative discovery shape for planning lanes: understand the current repo, compare against desirable standards, refine with the user, then emit issue-ready candidates for **`@gh-issue`**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Evidence sources

| Source | Libraries / actions | Output |
| --- | --- | --- |
| **Current repo** | [`read-repo-classification`](../../git/repo-classification/SKILL.md), [`read-dependencies-discover`](../../git/discover-dependencies/SKILL.md), [`read-repo-project-structure-eval`](../../git/project-structure-eval/SKILL.md), skim `README`, `docs/`, CI, `.cursor/tests/` | Pendencies, pillar gaps, 0–5 themes |
| **Open backlog** | [`read-issue-list`](../issue-list/SKILL.md) (optional) | Overlap hints vs existing issues |
| **Desirable standards** | Pack contracts in `skills/**`, repo docs, domain norms from chat | Desirables checklist |
| **Standards baseline** | Compare repo evidence to desirables | Gap notes (have / partial / missing) |

## Discovery loop (minimum)

Run **at least one refinement turn** after the first draft before proposing GitHub mutations.

1. **Goal** — One line: what discovery should optimize (backlog quality, hygiene, feature themes, …).
2. **Repo scan** — Run structure eval (+ optional dependency discovery summary). Capture **pendencies** (concrete, repo-specific).
3. **Desirables checklist** — Bullet list of what “good” looks like for this repo (tests green, docs aligned, skill DAG acyclic, labels on issues, …). Mark each **must** / **nice**.
4. **Standards baseline** — Table or bullets: desirable item → **Have** | **Partial** | **Missing** | **N/A** with short evidence.
5. **Draft themes** — 0–8 improvement themes; each theme: title, why it matters, suggested labels (0–3), rough verification.
6. **Refinement turn** — **AskQuestion**: prioritize themes, drop low-value items, add constraints, or **Sharpen** scope. Repeat until user signals **good spot** or **Ship to issues**.
7. **Issue candidate set** — For each retained theme, one row in the **candidate table** (below). Optionally cluster into multi-intent batch for **`@gh-issue`**.
8. **Handoff** — Paste long-form narrative + candidate table into **`@gh-issue`**; do **not** mutate GitHub from this library.

## Issue candidate table (chat)

| # | Title (draft) | Labels (draft) | Value | Execution pointer |
| --- | --- | --- | --- | --- |
| 1 | … | `enhancement`, `epic:<slug>` (if nested), … | Why this issue helps | `@gh-issue-view` → `@gh-issue-execute` or checklist |

When several rows belong to one epic, add a **Parent epic** row and mark children in the table; hand off with **`read-issue-nesting`** batch shape.

**Execution pointer** (required per row): the next **`@…`** skills after the issue exists (for example **`@gh-issue-execute`** after **`@gh-issue-view`**, or **`@gh-pr-review`** before **`@gh-pr`**).

## Multi-intent handoff to `@gh-issue`

When the user chooses **Ship to issues**:

- Pass a **single long narrative** covering all retained themes (context + desirables + gaps).
- Include the **candidate table**; let **`@gh-issue`** partition themes, dedupe per **`read-issue-dedupe`**, and decide **one vs many** creates/edits.
- Draft bodies may live under **`.cursor/gh/issue/<slug>.md`** per **`read-shuttle-gh-issue-commands`**.

## Do not

- Mutate git or GitHub from this file.
- Skip refinement when the user has not confirmed scope quality.
- Create issues without **`@gh-issue`** **Proceed**.

## See also

- [`read-issue-spec`](../issue-spec/SKILL.md) — issue body quality bar
- [`read-issue-dedupe`](../issue-dedupe/SKILL.md) — multi-intent clustering at **`@gh-issue`**
- [`read-issue-labels`](../issue-labels/SKILL.md) — label candidates
- [`@gh-issue`](../../../gh/issue/SKILL.md) · [`@gh-issue-backlog`](../../../gh/issue/backlog/SKILL.md)
