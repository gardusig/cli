---
name: read-issue-list
description: >-
  Deprecated redirect: issue list/search via read-shuttle-gh-issue-read (shuttle gh issue list|search).
---
# Internal: GitHub issue list (`read-issue-list`)

> **Deprecated.** Use [`read-shuttle-gh-issue-read`](../../read/shuttle/gh/issue-read/SKILL.md) — **`shuttle gh issue list|search`**. **Do not** embed raw `gh issue` bash fences.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Cadence (read-only)

Read-only inventory — no **Proceed** for list/search. Mutations → [`read-shuttle-gh-issue-commands`](../../read/shuttle/gh/issue-commands/SKILL.md) via owning **`@gh-*`** skill.

## Caller refinement

Pass flags on **`shuttle gh`**: `--state`, `--label`, `--limit`, `--repo` (from [`read-repo-stream`](../repo-stream/SKILL.md)).

## See also

- [`read-issue-dedupe`](../dedupe/SKILL.md)
- [`@gh-issue-list`](../../../gh/issue/list/SKILL.md)
