# Cursor Agent Skills

Reusable **Cursor Agent Skills** for GitHub issues and pull requests — backlog shaping, execution handoff, PR text, and review. Deterministic GitHub I/O runs through **[shuttle-cli](https://github.com/gardusig/shuttle-cli)** (`shuttle gh …`); agent skills decide *what* to do and gate mutations with structured Q&A.

Future public skills in this pack may cover other domains; they are not limited to repository hosting workflows.

## Install

```bash
./.cursor/scripts/install.sh
```

Install [shuttle-cli](https://github.com/gardusig/shuttle-cli) and authenticate `gh` before running **`@gh-*`** skills end-to-end.

Restart Cursor once after installing if `@` autocomplete does not show the skills.

Docs hub: [`docs/README.md`](docs/README.md) · GitHub skills: [`docs/gh.md`](docs/gh.md)

## Which skill?

| User intent | Start here |
| --- | --- |
| Open or update a PR | `@gh-pr` |
| Review a PR (AI) | `@gh-pr-review` |
| List or view PRs | `@gh-pr-list`, `@gh-pr-view` |
| Merge a PR | GitHub UI (after `@gh-pr-review` or `@gh-pr-view` verdict) |
| Shape / file issues | `@gh-issue` |
| Execute issue checkpoints | `@gh-issue-execute` |
| Backlog order / next child | `@gh-issue-backlog`, `@gh-issue-next` |
| Pick or view issues | `@gh-issue-pick`, `@gh-issue-view`, `@gh-issue-list` |
| Label hygiene | `@gh-issue-labels` |

Full `@gh-*` index: [`docs/gh.md`](docs/gh.md).

## Layout

- `skills/gh/` — public `@gh-*` orchestrators
- `skills/internal/read/` · `skills/internal/write/` — shared libraries (`read-*` / `write-*`)

## Delivery loop (summary)

1. **Discovery → issues:** chat/planning → `@gh-issue` (or inspect with `@gh-issue-backlog`)
2. **Implement:** `@gh-issue-next` / `@gh-issue-pick` → `@gh-issue-execute`
3. **PR:** `@gh-pr` → `@gh-pr-view` / `@gh-pr-review` → merge in GitHub UI

See [`docs/onboarding.md`](docs/onboarding.md) for expanded flows.

## Contributor checks

```bash
./.cursor/scripts/run.sh
```
