---
name: read-issue-split
description: >-
  Read-only: split one issue into epic + children or sibling issues — AI proposal before shuttle batch.
---
# Internal: Issue split (`read-issue-split`)

**Read-only library.** Propose how to **split** issue **#n** before **`shuttle gh issue batch`**.

## When

User asks to split an oversized issue, or **`@gh-issue`** detects multiple independent deliverables in one body.

## Proposal shape (chat)

| Row | Fields |
| --- | --- |
| Parent (optional) | keep #n as epic **or** close #n after split |
| New issues | title (with sequence prefix), one-line goal, labels |
| Edits | close/comment on #n, relink checklist |

## Execution (after Proceed)

1. Draft bodies under `.cursor/gh/issue/`
2. Write `batch.yaml` per [`read-shuttle-gh-issue-commands`](../../shuttle/gh/issue-commands/SKILL.md)
3. `shuttle gh issue batch --file batch.yaml --yes`

## See also

- [`read-issue-nesting`](../nesting/SKILL.md)
- [`read-issue-consolidate`](../consolidate/SKILL.md)
