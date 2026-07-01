---
name: read-issue-description-review-report
description: >-
  Read-only: issue review / reshape report scaffold and fixed step order. Parent read-issue-description.
  Consumer: @gh-issue-review.
---
# Issue review report (`@gh-issue-review`)

**Consumer:** **`@gh-issue-review`**. **No** GitHub mutations.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Fixed order

1. **`read-dependencies-discover`** — repo context (full pass; no **`write-quality-evaluate`** unless user asks for **`@git-review`**).
2. **`read-issue-view`** — target issue JSON (+ comments when needed).
3. **`read-issue-list`** + **[`read-issue-dedupe` dedupe-checklist](../../issue-dedupe/dedupe-checklist/SKILL.md)** — peer inventory.
4. **`read-issue-dedupe`** — overlap verdict on reshaped candidate (ignore self **`#N`** on reshape).
5. **Synthesis** — map asks to paths from discovery; gaps vs **`read-issue-spec`**.
6. **`read-safety-structured-qa`** — when priority, scope split, or duplicate resolution is unclear.
7. **Report** (sections below) → hand off **`@gh-issue`** after user **Proceed**.

## Report sections

1. **Target snapshot** — title, state, labels, URL, body summary.
2. **Codebase fit** — files/areas tied to the ask (from discovery).
3. **Peer overlaps** — table of related open issues + dedupe verdict.
4. **Gaps** — missing acceptance, examples, non-regression ( **`read-issue-spec`** checklist).
5. **Proposed reshape** (optional) — draft title/body bullets for **`@gh-issue`**.

## See also

- [`@gh-issue-review`](../../../../gh/issue/review/SKILL.md)
- [`read-issue-spec`](../../issue-spec/SKILL.md)
- [`read-issue-dedupe`](../../issue-dedupe/SKILL.md)
