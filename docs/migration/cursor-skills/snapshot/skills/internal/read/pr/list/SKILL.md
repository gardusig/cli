---
name: read-pr-list
description: >-
  Deprecated redirect: PR list/view/diff via read-shuttle-gh-pr-read and read-shuttle-git.
---
# Internal: GitHub pull request list / view (`read-pr-list`)

> **Deprecated.** Use [`read-shuttle-gh-pr-read`](../../read/shuttle/gh/pr-read/SKILL.md) and [`read-shuttle-git`](../../read/shuttle/git/SKILL.md). **Do not** embed raw `gh pr` or `git branch` bash fences.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## List / view / diff

See **`read-shuttle-gh-pr-read`** for:

- open/closed/merged lists (`--state`, `--head`, `--base`, `--limit`)
- single PR view JSON
- diff stat

## PR from current branch

```bash
shuttle gh --format json pr list --head "$(shuttle git branch-current)" --state open --limit 20
```

## See also

- [`read-shuttle-gh-pr-commands`](../../read/shuttle/gh/pr-commands/SKILL.md)
- [`list-view-hub/SKILL.md`](./list-view-hub/SKILL.md)
- [`@gh-pr-list`](../../../gh/pr/list/SKILL.md)
