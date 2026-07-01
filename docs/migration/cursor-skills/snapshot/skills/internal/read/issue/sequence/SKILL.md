---
name: read-issue-sequence
description: >-
  Read-only: title sequence prefix rules (N — epic, N.M — child), parse/sort contract shared with shuttle gh backlog.
---
# Internal: Issue sequence (`read-issue-sequence`)

**Read-only library.** Title prefix conventions for ordered backlogs. **Parse/sort** is implemented in shuttle-cli **`shuttle gh backlog`**; this file documents the contract for **`@gh-issue`** and **`@gh-issue-backlog`**.

## Title format

| Kind | Pattern | Example |
| --- | --- | --- |
| Epic | `N — Title` | `1 — GitHub integration (epic)` |
| Child | `N.M — Title` | `1.1 — shuttle gh foundation` |

Use em dash **`—`** between prefix and title. **`N`** and **`M`** are integers without leading zeros.

## Labels (with sequence)

| Label | On |
| --- | --- |
| `issue-type:epic` | parent |
| `issue-type:child` | children |
| `epic:<slug>` | parent + all children |

## AI-side operations

| Operation | cursor-skills | shuttle |
| --- | --- | --- |
| Propose next epic number | scan open issues in chat | `shuttle gh backlog tree` |
| Assign child sequence | draft titles before batch | `shuttle gh issue batch` |
| Reprefix after reorder | write `plan.yaml` | `shuttle gh backlog resequence --file plan.yaml --yes` |
| Pick next work | `@gh-issue-next` | `shuttle gh backlog next` |

## Resequence plan YAML

```yaml
renames:
  - number: 42
    title: "1.2 — Renamed child"
```

## See also

- [`read-issue-nesting`](../nesting/SKILL.md)
- [`read-shuttle-gh`](../../shuttle/gh/SKILL.md)
