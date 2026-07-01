---
name: read-skill-suggestions-next-steps-options
description: >-
  Read-only: ranked next-step option catalog for public @gh-* skills.
  Used to choose the top 1-3 suggested follow-up skills.
---

# Internal: next-steps options catalog

Rows are impact-ordered. For each `CURRENT_SKILL`, use the first 1-3 rows whose **When** applies.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

### `gh-issue-execute`

| Suggest | When |
| --- | --- |
| **`@gh-pr`** | Checkpoints complete |
| **`@gh-pr-review`** | User wants acceptance review before PR |
| Done | Execution paused |

### `gh-issue`

| Suggest | When |
| --- | --- |
| **`@gh-issue-backlog`** | Scope needs ordering / epic view |
| **`@gh-issue-view`** | User picked an issue |
| **`@gh-issue-execute`** | Plan ready |

### `gh-issue-backlog`

| Suggest | When |
| --- | --- |
| **`@gh-issue-next`** | Pick next child |
| **`@gh-issue-labels`** | Label hygiene |
| Done | Tree review complete |

### `gh-issue-next`

| Suggest | When |
| --- | --- |
| **`@gh-issue-view`** | Inspect chosen issue |
| **`@gh-issue-execute`** | Start implementation |
| **`@gh-issue-pick`** | User wants manual pick |

### `gh-issue-labels`

| Suggest | When |
| --- | --- |
| **`@gh-issue-backlog`** | Verify sort after labelize |
| **`@gh-issue-list`** | Verify open issues per label |
| Done | Label pass complete |

### `gh-issue-close`

| Suggest | When |
| --- | --- |
| **`@gh-issue-list`** | Inventory remaining issues |
| Done | Close workflow complete |

### `gh-issue-delete-closed`

| Suggest | When |
| --- | --- |
| **`@gh-issue-list`** | More closed issues to review |
| Done | Delete workflow complete |

### `gh-issue-list`

| Suggest | When |
| --- | --- |
| **`@gh-issue-pick`** | User wants structured pick |
| **`@gh-issue-view`** | User named one issue |
| **`@gh-issue`** | User wants to create/edit |

### `gh-issue-pick`

| Suggest | When |
| --- | --- |
| **`@gh-issue-view`** | Re-read issue before work |
| **`@gh-issue-execute`** | Ready to implement |

### `gh-issue-review`

| Suggest | When |
| --- | --- |
| **`@gh-issue`** | Reshape approved; apply edits |
| **`@gh-issue-backlog`** | Themes need ordering |
| Done | Review-only pass complete |

### `gh-issue-view`

| Suggest | When |
| --- | --- |
| **`@gh-issue-execute`** | Ready to implement (checkpoints in issue/chat) |
| **`@gh-issue`** | User wants to edit issue text |

### `gh-pr`

| Suggest | When |
| --- | --- |
| **`@gh-pr-view`** | PR created/edited; inspect on GitHub |
| **`@gh-pr-review`** | User wants deeper review |
| Done | PR workflow complete for this branch |

### `gh-pr-close`

| Suggest | When |
| --- | --- |
| **`@gh-pr-list`** | Inventory open PRs |
| Done | Close workflow complete |

### `gh-pr-list`

| Suggest | When |
| --- | --- |
| **`@gh-pr-view`** | User picked one PR |
| **`@gh-pr`** | User wants create/edit |

### `gh-pr-review`

| Suggest | When |
| --- | --- |
| **`@gh-pr-view`** | Confirm merge in GitHub UI |
| **`@gh-pr`** | PR needs title/body update |
| **`@gh-issue`** | Gaps need new/edited issues |

### `gh-pr-view`

| Suggest | When |
| --- | --- |
| **`@gh-pr-review`** | User wants full acceptance review |
| **`@gh-pr`** | Update PR body/title |
| Done | Merge-ready — user merges in GitHub UI |

## See also

- [`read-skill-suggestions`](../SKILL.md)
