---
name: read-issue-view
description: >-
  Deprecated redirect: issue view via read-shuttle-gh-issue-read (shuttle gh issue view).
---
# Internal: GitHub issue view (`read-issue-view`)

> **Deprecated.** Use [`read-shuttle-gh-issue-read`](../../read/shuttle/gh/issue-read/SKILL.md) — **`shuttle gh issue view`**. **Do not** embed raw `gh issue view` bash fences.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Usage

```bash
shuttle gh --format json issue view <N>
shuttle gh --format json issue view <N> --comments
```

Add **`--repo owner/repo`** on **`shuttle gh`** when not in default context.

## See also

- [`read-shuttle-gh-issue-commands`](../../read/shuttle/gh/issue-commands/SKILL.md)
- [`@gh-issue-view`](../../../gh/issue/view/SKILL.md)
