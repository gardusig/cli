---
name: read-shuttle-git
description: >-
  Read-only: shuttle git read command shapes for branch, diff, log, remote, rev-parse.
  All local git introspection in cursor-skills uses shuttle git — no raw git bash fences.
---
# Internal: shuttle git read (`read-shuttle-git`)

**Read-only library.** Local git inventory via **`shuttle git`** read subcommands. Mutating git work uses existing **`shuttle git`** shortcuts (push, commit, main, …).

Parent integration: [`read-shuttle-gh`](./gh/SKILL.md)

## Tooling

| Tool | Requirement |
| --- | --- |
| **`shuttle`** | On PATH |
| **`git`** | Local repo (shuttle wraps git) |

## Branch

```bash
shuttle git branch-current
```

## Diff vs PR base (`$BASE_GIT`)

```bash
shuttle git diff-stat --base "$BASE_GIT"
shuttle git diff-names --base "$BASE_GIT"
```

## Log (PR delta / issue keywords)

```bash
shuttle git log-oneline --base "$BASE_GIT"
shuttle git log-messages --base "$BASE_GIT" --max-count 30
```

## Ahead / behind

```bash
shuttle git rev-list-count --base "$BASE_GIT"
```

## Remote / ref resolution (`read-repo-stream`)

```bash
shuttle git remote-url upstream
shuttle git remote-url origin
shuttle git rev-parse upstream/main
shuttle git merge-base-check --base "$BASE_GIT"
```

## Publish readiness (`read-pr-branch-context`)

```bash
shuttle git rev-parse HEAD
shuttle git publish-check --remote origin --branch "$HEAD_BRANCH"
```

## PR lookup by branch

Combine with [`read-shuttle-gh-pr-read`](./gh/pr-read/SKILL.md):

```bash
shuttle gh --format json pr list --head "$(shuttle git branch-current)" --state open --limit 20
```

## See also

- [shuttle-cli docs/git.md](https://github.com/gardusig/shuttle-cli/blob/main/docs/git.md)
- [`read-repo-stream`](../repo/stream/SKILL.md)
- [`read-diff-summary-delta-narrative`](../diff/summary/delta-narrative/SKILL.md)
