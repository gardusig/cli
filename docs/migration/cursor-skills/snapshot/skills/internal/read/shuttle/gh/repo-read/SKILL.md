---
name: read-shuttle-gh-repo-read
description: >-
  Read-only: shuttle gh repo view for templates and nameWithOwner. Parent read-shuttle-gh.
---
# Internal: shuttle gh repo read (`read-shuttle-gh-repo-read`)

**Read-only library.** Repository metadata via **`shuttle gh repo view`**.

Parent: [`read-shuttle-gh`](../SKILL.md)

## Default metadata

```bash
shuttle gh --format json repo view
```

## Issue + PR templates

```bash
shuttle gh --format json repo view --json-fields nameWithOwner,owner,issueTemplates,pullRequestTemplates
```

## Template count only (jq optional)

Parse JSON from shuttle output in chat — do not run raw `gh repo view` fences.

## See also

- [`read-repo-forms-json`](../../repo/forms-json/SKILL.md) — field semantics (deprecated fences removed)
