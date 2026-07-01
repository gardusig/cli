---
name: read-issue-labels
description: >-
  Read-only: list repo labels, propose 0–3 candidates from title/body, match or suggest gh label create; command
  shapes in label-decorate/SKILL.md. Caller: gh-issue. Does not run gh writes or AskQuestion.
---
# Internal: Issue labels (`read-issue-labels`)

**Read-only library.** After **[`read-issue-description`](../issue-description/SKILL.md)** has set shape and you have a **draft title + body** (or the user supplied them), use this playbook to propose **GitHub labels**. **No** `gh label create`, **no** `gh issue create` / `edit` flags—**callers** run **AskQuestion** / structured confirm per **[`read-safety-skill-safety`](../../../internal/read/safety/skill-safety/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## 1. Inventory existing labels

Run the **Inventory (read-only)** command block in **[`label-decorate/SKILL.md`](./label-decorate/SKILL.md)** (same auth as other `gh` skills).

Treat **exact name matches** (case-sensitive per GitHub) as **reuse**. Prefer **existing** labels over inventing new ones.

---

## 2. Propose 0–3 candidates

From **title + first paragraph / acceptance criteria** in the body:

1. **Epic family** (when **`read-issue-nesting`** applies) — propose **`epic:<slug>`** and **`issue-type:epic`** or **`issue-type:child`**; these **count toward** the three-label soft cap only when **not** in an epic batch (epic flows may use up to **five** labels with one-line justification in chat).
2. **Area / domain** — e.g. paths `skills/gh/`, `docs/` → tokens like `area:skills`, `area:docs` only if the repo already uses that pattern; otherwise use **one** short area token consistent with existing names.
3. **Type** — `bug`, `enhancement`, `documentation` only if an **existing** label matches or the repo uses GitHub defaults.
4. **Stop at three** (non-epic) — do not spam labels; omit if nothing fits.

**Naming hygiene** (new labels only—see **[`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md)** §2 for “short label” spirit):

- Lowercase, **hyphens** not spaces; **no** emoji in label names.
- Prefer **one** new label over three near-duplicates.

---

## 3. Match vs create

For each **candidate**:

- **Fuzzy match** an existing label (substring, plural/singular, `docs` vs `documentation`) → **map** to the existing name in the proposal table.
- **No reasonable match** → mark **`needs_create`** with a one-line **description** and a neutral **`--color`** (e.g. `ededed` or repo palette if documented).

**Caller:** If any **`needs_create`**, summarize **`gh label create NAME --color … --description "…"`** and obtain **structured confirm** before running **`gh label create`**. Then pass **`--label a,b`** on **`gh issue create`** or **`gh issue edit --add-label`** (confirm already required for those mutations).

---

## 4. Hand off

Return to **`@gh-issue`**: attach labels in the chosen create-or-edit mutation path when the user Proceeds with a non-empty set; skip labels when the user declines.

## See also

- **[`read-issue-dedupe`](../issue-dedupe/SKILL.md)** — run **before** description for new issues.
- **[`read-issue-description`](../issue-description/SKILL.md)** — templates vs pack body.
