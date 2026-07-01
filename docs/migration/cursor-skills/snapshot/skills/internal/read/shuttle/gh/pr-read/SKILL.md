---
name: read-shuttle-gh-pr-read
description: >-
  Read-only: shuttle gh pr list/view/diff command shapes. Parent read-shuttle-gh.
---
# Internal: shuttle gh PR read (`read-shuttle-gh-pr-read`)

**Read-only library.** PR inventory via **`shuttle gh`**.

Parent: [`read-shuttle-gh`](../SKILL.md)

## List

```bash
shuttle gh --format json pr list --state open --limit 30
```

## View

```bash
shuttle gh --format json pr view <N>
```

## Diff stat

```bash
shuttle gh pr diff <N>
```

## See also

- [`read-pr-list`](../../../pr/list/SKILL.md) — legacy (deprecated)
