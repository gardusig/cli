---
name: read-issue-consolidate
description: >-
  Read-only: merge overlapping issues — AI proposal before shuttle edit/close batch.
---
# Internal: Issue consolidate (`read-issue-consolidate`)

**Read-only library.** Propose **merge/consolidate** before shuttle mutations.

## When

**`read-issue-dedupe`** finds near-duplicates, or user asks to merge issues.

## Proposal shape (chat)

| Row | Action |
| --- | --- |
| **Canonical** | #n — keep this body/title |
| **Merge in** | #m — fold scope into canonical |
| **Close** | #k — duplicate with comment linking canonical |
| **Labels** | unified label set on canonical |

## Execution (after Proceed)

1. Edit canonical issue body/title via `shuttle gh issue edit … --yes`
2. Close duplicates via `shuttle gh issue close … --yes`
3. Optional label batch via `shuttle gh issue edit --add-label … --yes`

## See also

- [`read-issue-dedupe`](../dedupe/SKILL.md)
- [`read-issue-split`](../split/SKILL.md)
