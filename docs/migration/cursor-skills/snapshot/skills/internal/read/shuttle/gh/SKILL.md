---
name: read-shuttle-gh
description: >-
  Read-only: integration contract between cursor-skills @gh-* skills and shuttle-cli `shuttle gh`
  commands. No gh/bash fences in public skills — agents invoke shuttle for deterministic GitHub I/O.
---
# Internal: shuttle-cli GitHub integration (`read-shuttle-gh`)

**Read-only library.** Normative mapping from **`@gh-issue-*`** / **`@gh-pr-*`** skills to **[shuttle-cli](https://github.com/gardusig/shuttle-cli)** `shuttle gh` subcommands. Implementation lives in shuttle-cli epic **01** ([#34](https://github.com/gardusig/shuttle-cli/issues/34) — foundational git/gh/docker layer).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first.

## Two-repo split

| Layer | Owner | Role |
| --- | --- | --- |
| **Judgment** | cursor-skills (`read-issue-dedupe`, split/consolidate, body templates) | *What* to do — overlap, partition, draft bodies, chat **AskQuestion** |
| **Mechanics** | shuttle-cli (`shuttle gh …`) | *How* to call GitHub — list, create, edit, close, labels, PRs, backlog tree |

Public **`@gh-*` skills must not embed** raw `gh issue`, `gh pr`, or `gh label` bash fences. Call **`shuttle gh …`** instead (see command map below).

## Tooling (Before batch)

| Tool | Requirement |
| --- | --- |
| **`shuttle`** | On PATH — install from [shuttle-cli](https://github.com/gardusig/shuttle-cli) (`./scripts/install.sh`) |
| **`gh`** | Authenticated (`gh auth status`) — shuttle gh provider wraps `gh` |

## Double-gate contract

| Context | cursor-skills | shuttle write |
| --- | --- | --- |
| Agent after **Proceed** | **AskQuestion** summary in chat | append **`--yes`** (skip shuttle interactive gate) |
| Human in terminal | — | interactive gate or **`--yes`** |
| Read-only inventory | no gate | no **`--yes`** needed |

Shuttle reuses **`require_write_gate`** from `shuttle/internal/write/gate.py` (same as `shuttle git`).

## Command map (target — shuttle-cli epic 01)

**Global flags:** `--repo owner/name`, `--format json` (default for agents).

### Issue read (no gate)

| Skill / library | shuttle command |
| --- | --- |
| `@gh-issue-list`, `read-issue-list` | `shuttle gh issue list [--state] [--label] [--limit] --format json` |
| `@gh-issue-view`, `read-issue-view` | `shuttle gh issue view <n> [--comments] --format json` |
| `read-issue-dedupe` search | `shuttle gh issue search <query> --format json` |

### Issue write (gate unless `--yes`)

| Skill | shuttle command |
| --- | --- |
| `@gh-issue` create | `shuttle gh issue create --title … --body-file … [--label …]` |
| `@gh-issue` edit | `shuttle gh issue edit <n> …` |
| `@gh-issue-close` | `shuttle gh issue close <n> [--comment …]` |
| `@gh-issue-delete-closed` | `shuttle gh issue delete <n>` |
| `@gh-issue` batch (epic + children) | `shuttle gh issue batch --file batch.yaml` |

Legacy shapes until migration completes: [`write-issue-commands`](../../write/issue/commands/SKILL.md) — **deprecated**; prefer shuttle.

### Label

| Skill | shuttle command |
| --- | --- |
| `@gh-issue-labels` inventory | `shuttle gh label list --format json` |
| `@gh-issue-labels` sync | `shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml` |
| `@gh-issue-labels` delete stale | `shuttle gh label delete <name>` |

Manifest: [`.cursor/gh/labels.manifest.yaml`](../../../../../../.cursor/gh/labels.manifest.yaml) (when present in target repo).

### PR

| Skill | shuttle command |
| --- | --- |
| `@gh-pr-list`, `read-pr-list` | `shuttle gh pr list … --format json` |
| `@gh-pr-view` | `shuttle gh pr view <n> … --format json` |
| `@gh-pr` create/edit | `shuttle gh pr create` / `edit` |
| `@gh-pr-close` | `shuttle gh pr close <n>` |

**Merge:** not a public skill — users merge in the GitHub UI; optional `shuttle gh pr merge` exists in shuttle-cli for terminal use only.

Legacy: [`write-pr-commands`](../../write/pr/commands/SKILL.md) — **deprecated**; prefer shuttle.

### Backlog (deterministic — shuttle only)

| Skill | shuttle command |
| --- | --- |
| `@gh-issue-backlog` | `shuttle gh backlog tree --format json` |
| `@gh-issue-next` | `shuttle gh backlog next --format json` |
| resequence | `shuttle gh backlog resequence --file plan.yaml` |

Sequence title rules: [`read-issue-sequence`](../issue/sequence/SKILL.md) (when added) — parse/sort contract shared with shuttle **01g**.

## Child libraries

| Library | Role |
| --- | --- |
| [`read-shuttle-gh-issue-read`](issue-read/SKILL.md) | Issue list/view/search |
| [`read-shuttle-gh-issue-commands`](issue-commands/SKILL.md) | Issue write + batch |
| [`read-shuttle-gh-pr-read`](pr-read/SKILL.md) | PR list/view/diff |
| [`read-shuttle-gh-pr-commands`](pr-commands/SKILL.md) | PR write |
| [`read-shuttle-gh-label-read`](label-read/SKILL.md) | Label list/sync/delete |
| [`read-shuttle-gh-repo-read`](repo-read/SKILL.md) | Repo templates + identity |
| [`read-shuttle-git`](../git/SKILL.md) | Local git read (diff, log, remote) |

## Migration status

| Phase | cursor-skills | shuttle-cli |
| --- | --- | --- |
| **Now** | Child libs under `read-shuttle-gh-*`; public skills invoke **`shuttle gh`** | Epic **01** implemented — [`docs/gh.md`](https://github.com/gardusig/shuttle-cli/blob/main/docs/gh.md) |
| **Skills** | `@gh-issue-labels`, `@gh-issue-backlog`, `@gh-issue-next` (16 public `@gh-*` skills) | `shuttle gh backlog`, `label sync`, `issue batch` |

## Do not

- Add new raw `gh issue` / `gh pr` fences to public `@gh-*` skills.
- Skip cursor **Proceed** before shuttle write commands (unless user explicitly overrides).
- Assume shuttle commands exist — check `shuttle gh --help`; legacy internal libs are deprecated fallbacks only.

## See also

- [shuttle-cli](https://github.com/gardusig/shuttle-cli) · canonical plan [`.cursor/plans/cursor-skills.plan.md`](../../../../../../.cursor/plans/cursor-skills.plan.md)
- [`docs/gh.md`](../../../../../../docs/gh.md) — public gh skill hub
- [`read-issue-nesting`](../../issue/nesting/SKILL.md) — epic body shape (unchanged; shuttle executes creates)
