---
name: read-repo-forms-json
description: >-
  Read-only: repo templates and identity via read-shuttle-gh-repo-read (shuttle gh repo view).
---
# Internal: repo forms JSON (`read-repo-forms-json`)

**Read-only library.** Template and repo identity via [`read-shuttle-gh-repo-read`](../../read/shuttle/gh/repo-read/SKILL.md). **Do not** embed raw `gh repo view` bash fences.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Pull request templates

| Case | Command |
| --- | --- |
| Same-repo | `shuttle gh --format json repo view --json-fields pullRequestTemplates` |
| Fork / upstream | `shuttle gh --repo "$UPSTREAM" --format json repo view --json-fields pullRequestTemplates` |

## Issue templates

| Case | Command |
| --- | --- |
| Default context | `shuttle gh --format json repo view --json-fields issueTemplates` |
| Upstream | `shuttle gh --repo "$UPSTREAM" --format json repo view --json-fields issueTemplates` |

## Combined fetch

```bash
shuttle gh --format json repo view --json-fields nameWithOwner,owner,issueTemplates,pullRequestTemplates
```

Parse JSON in chat — optional **`jq`** on shuttle stdout, not raw **`gh`**.

## Repo identity

Included in default **`repo view`** fields — see **`read-shuttle-gh-repo-read`**.

## See also

- [`read-repo-stream`](../repo-stream/SKILL.md)
- [`read-pr-description`](../pr/description/SKILL.md)
- [`read-issue-description`](../issue/description/SKILL.md)
