---
name: read-issue-dedupe
description: >-
  Read-only: list/search open issues, flag near-duplicates vs one or more candidate title+body rows; no gh writes.
  Pasteable checklist: ./dedupe-checklist/SKILL.md. Callers: @gh-issue, @gh-issue-review.
---
# Internal: Issue dedupe (`read-issue-dedupe`)

**Read-only library.** Compare **one or more candidate** issues (each: title + summary lines) to **open** issues using **`gh`**. **No** `gh issue create`, **no** comments, **no** closes.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

1. Follow **[`dedupe-checklist/SKILL.md`](./dedupe-checklist/SKILL.md)** (**§1** defers all **`gh issue list`** / **`gh search issues`** shapes to **`read-issue-list`**—**do not** duplicate flags here).
2. Emit a short verdict **per candidate**: **`safe_to_create`** | **`likely_duplicate #n`** | **`ambiguous`** (list candidate numbers + one-line reason each). For a **single** candidate, one verdict is enough.

**Reshape-review (optional caller: `@gh-issue-review`).** When the **candidate** text describes **refining existing issue `#N`**, treat a hit on **`#N` itself** as **self**, not a duplicate signal—only **other** numbers are **peer overlaps** or **likely duplicate** targets. Verdict labels stay the same; interpret **`likely_duplicate #m`** as “**`#m`** collides with the reshaped scope.”

## `@gh-issue` orchestration order

Use this sequence when `@gh-issue` routes create-or-update behavior.

### Single candidate (default)

1. **List / search** — run `@gh-issue-list` (or equivalent via [`read-issue-list`](../issue-list/SKILL.md) + [`dedupe-checklist/SKILL.md`](./dedupe-checklist/SKILL.md)) to inventory open issues before any write.
2. **Dedupe verdict** — evaluate candidate title + body summary through this skill and return `safe_to_create` | `likely_duplicate #n` | `ambiguous`.
3. **Branch**
   - `likely_duplicate #n` (or `ambiguous` resolved to a single `#n`) -> treat as update path in `@gh-issue`.
   - `safe_to_create` -> continue create path in `@gh-issue`.

### Multi-candidate (optional `@gh-issue`)

After **`@gh-issue`** has **partitioned themes** per **[Multi-intent clustering](#multi-intent-clustering)** below:

1. **List / search once** — same inventory pass as single-candidate step 1; reuse the same open-issue set for every theme. Optionally add a focused **`gh search issues`** query per theme only when the default list is too large to compare fairly.
2. **Per-theme verdict** — for each theme, compare its working title + one-line intent to that inventory; emit `safe_to_create` | `likely_duplicate #n` | `ambiguous` **per row**. **Never** skip this for a theme that will end in **create**.
3. **Merge similar themes before publish** — when two rows point at the same **`likely_duplicate #n`** or are clearly the same root cause, default to **one** issue (merge rows in the summary table); user confirms.
4. **Aggregate** — hand off a table (theme → verdict → proposed **edit #n** or **create**) to **`@gh-issue`** for structured Q&A and one **Proceed — batch** per **`read-safety-structured-qa`**.

If clustering collapses to **one** theme, use **only** the single-candidate subsection above.

## Multi-intent clustering

Optional path after **Ship** on the pre-dedupe gate. Consumer: **`@gh-issue`**.

### When to use

After **Ship**, if **any** of:

- the user asks to split into multiple issues;
- the pasted request has **clearly disjoint** workstreams (unrelated bullets/sections);
- a long paste has **≥2** themes that do not share one root cause.

If clustering yields **one** theme, use **Single candidate** only.

### Steps

1. **Partition** — Group bullets/sections by shared root cause (two bullets, one auth flow → **one** theme).
2. **Inventory once** — **`read-issue-list`** + **[`dedupe-checklist/SKILL.md`](./dedupe-checklist/SKILL.md)**; reuse for every theme.
3. **Per-theme dedupe** — Run **Multi-candidate** verdicts above; **never** skip dedupe for a theme that will **create**.
4. **Summarize** — Table: Theme → verdict → **edit #n** / **create** / **defer**; offer to merge near-duplicate themes.
5. **Structured Q&A** — **Abort**, **Defer selected themes**, or **Proceed — batch** (§1d multi-issue; mutations via **`read-shuttle-gh-issue-commands`**).
6. **Artifacts** — Draft bodies under **`.cursor/gh/issue/`**; **`read-issue-description`** + **`read-issue-labels`** per non-deferred theme before one mutation summary.

### Fixture (verification)

**Input:** six bullets—(1–2) auth timeout + refresh retry, (3) CSV export, (4–5) README + docs hub, (6) CI migration.

**Expected:** four themes (auth, export, docs, CI) unless inventory shows an open CI issue → **edit #n** for that row only.

Optional first pass: run `@gh-issue-review` on an existing issue when the body is weak and needs codebase + overlap analysis before deciding update vs create.

## Do not

- Mutate GitHub state.
- Duplicate **`gh issue list`** / **`gh search issues`** recipes outside **`read-issue-list`** — the **checklist** template links there too.

## See also

- **[`read-issue-list`](../issue-list/SKILL.md)** — normative list/search **`gh`** lines.
- [`@gh-issue`](../../../gh/issue/SKILL.md) · [`@gh-issue-review`](../../../gh/issue/review/SKILL.md)
- [`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md)
