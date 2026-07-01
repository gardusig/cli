---
name: read-shuttle-gh-issue-read
description: >-
  Read-only: shuttle gh issue list/view/search command shapes. Parent read-shuttle-gh.
  Replaces raw gh fences in read-issue-list and read-issue-view.
---
# Internal: shuttle gh issue read (`read-shuttle-gh-issue-read`)

**Read-only library.** Invoke **`shuttle gh`** for issue inventory — no raw `gh issue` bash fences.

Parent: [`read-shuttle-gh`](../SKILL.md)

## Tooling

| Tool | Requirement |
| --- | --- |
| **`shuttle`** | On PATH |
| **`gh`** | Authenticated (`gh auth status`) |

Append **`--repo owner/name`** when not in default context. Default **`--format json`** for agents.

## List open inventory

```bash
shuttle gh --format json issue list --state open --limit 30
```

Filter by label:

```bash
shuttle gh --format json issue list --state open --label bug --limit 30
```

## View single issue

```bash
shuttle gh --format json issue view <N>
```

With comments:

```bash
shuttle gh --format json issue view <N> --comments
```

## Search

```bash
shuttle gh --format json issue search "QUERY" --limit 30
```

## List closed (bulk delete preview)

```bash
shuttle gh --format json issue list --state closed --limit 200
```

## See also

- [`read-issue-list`](../../../issue/list/SKILL.md) — legacy (deprecated)
- [`read-issue-view`](../../../issue/view/SKILL.md) — legacy (deprecated)
