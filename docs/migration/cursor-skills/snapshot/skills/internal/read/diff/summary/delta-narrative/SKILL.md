---
name: read-diff-summary-delta-narrative
description: >-
  Read-only: PR/commit delta narrative; shell recipes via read-shuttle-git (shuttle git diff/log).
---
# Git diff summary (commit message or PR prep)

Reusable shape for summarizing branch delta before a **commit message** or **PR body**. **Normative commands** live in [`read-shuttle-git`](../../shuttle/git/SKILL.md).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Steps (human or agent)

1. **Inventory** — group changed areas from **`shuttle git diff-names --base "$BASE_GIT"`**.
2. **Themes** — from **`shuttle git log-oneline --base "$BASE_GIT"`**, group into **2–5 bullets**.
3. **Risk** — one line: merge risk, behavior change, or none.
4. **Omit** — noise renames unless that is the story.

## Shell recipes (via shuttle)

```bash
shuttle git log-oneline --base "$BASE_GIT"
shuttle git diff-names --base "$BASE_GIT"
shuttle git merge-base-check --base "$BASE_GIT"
shuttle git log-messages --base "$BASE_GIT" --max-count 30
```

Use **two-dot** log ranges via **`--base`** / **`--head`** on shuttle git commands.

## Commit message skeleton (short)

```
<area>: <imperative outcome>

- <bullet tied to diff>

Refs: #n
```

## Hand-off

- [`read-diff-summary`](../SKILL.md)
- [`read-pr-description`](../../pr/description/SKILL.md)
