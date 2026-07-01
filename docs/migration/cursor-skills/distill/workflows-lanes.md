---
name: read-workflow-workflows
description: >-
  Read-only in-pack GitHub workflow references for public @gh-* skills: issue shaping,
  execution checkpoints, PR create/edit, and review. Merge happens in GitHub UI.
---
# In-pack GitHub workflows

Reference lanes for **`@gh-issue-*`** and **`@gh-pr-*`** skills. Local repository operations (branch, commit, push, cleanup) are **out of scope** for this pack. **PR merge** is **out of scope** — users merge in the GitHub UI after review.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Public skill map

| Invoke | Workflow section |
| --- | --- |
| **`@gh-issue-execute`** | [Issue execution workflow](#issue-execution-workflow) |
| **`@gh-issue`** | [Issue create/edit workflow](#issue-createedit-workflow) |
| **`@gh-issue-backlog`** · **`@gh-issue-next`** | [Backlog workflow](#backlog-workflow) |
| **`@gh-pr`** | [PR create/edit workflow](#pr-createedit-workflow) |
| **`@gh-pr-review`** | [PR review workflow](#pr-review-workflow) |

High-risk GitHub mutations must run behind [`read-safety-skill-safety`](../../safety/skill-safety/SKILL.md) and [`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md).

## Backlog workflow

1. Inspect order via **`@gh-issue-backlog`** (`shuttle gh backlog tree`).
2. Pick next child via **`@gh-issue-next`** or manual **`@gh-issue-pick`**.
3. Hand off to **`@gh-issue-view`** → **`@gh-issue-execute`**.

## Issue execution workflow

1. Confirm checkpoint order from issue body or chat.
2. Execute checkpoints with verification evidence per item.
3. Optional **`@gh-pr-review`** before **`@gh-pr`** when the user wants acceptance review.
4. Hand off to **`@gh-pr`** when complete (user ensures branch is published separately).

## Issue create/edit workflow

1. **Preflight** — Sharpen / Abort / Ship.
2. **Dedupe** — **`read-issue-dedupe`** against open issues.
3. **Write gate** before **`read-shuttle-gh-issue-commands`** (`shuttle gh … --yes`).

## PR create/edit workflow

1. **Preflight** — **`read-pr-preflight-qa`** + **`read-pr-branch-context`** (branch intent, publish readiness).
2. **Prevalidate** — **`read-pr-prevalidate`** (discover → install → evaluate) unless skipped.
3. Optional **`@gh-pr-review`**.
4. **PR lookup** — **`read-shuttle-gh-pr-read`** + disambiguation gate when needed.
5. **Draft** — **`read-pr-description`** (templates, delta, issue linking, title/body).
6. **§9 apply** — **`read-shuttle-gh-pr-commands`** after Proceed.

## PR review workflow

1. Load PR via **`read-shuttle-gh-pr-read`** view shapes.
2. Compare against linked issues via **`@gh-issue-view`** when present.
3. Deliver verdict and next invoke (`@gh-pr`, `@gh-issue`, merge in GitHub UI, …).

## See also

- [`read-workflow-git`](./git/SKILL.md) — index of workflow libraries
- [`read-pr-content-pr-orchestration`](../../pr/content/pr-orchestration/SKILL.md) — **`@gh-pr`** fixed order
