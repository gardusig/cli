# Pack onboarding (GitHub skills)

Human reference for **`@gh-*`** skills. Operational contracts live in **`skills/**/SKILL.md`** and internal libraries under `skills/internal/`.

**Tooling:** [shuttle-cli](https://github.com/gardusig/shuttle-cli) on PATH + authenticated `gh`. Public skills invoke **`shuttle gh …`** via [`read-shuttle-gh`](../skills/internal/read/shuttle/gh/SKILL.md) libraries — not raw `gh` bash fences.

## Install and verify

From this repo root:

```bash
./.cursor/scripts/install.sh
```

Useful options:

- `--clean` — wipe **`CURSOR_SKILLS_DIR`**, then reinstall this pack
- `--uninstall` — remove only this pack’s folders (confirm with `DELETE` or `CURSOR_SKILLS_UNINSTALL_CONFIRM=yes`)
- `--verify-only`, `--dry-run`, `--repo DIR`
- `CURSOR_SKILLS_DIR` — destination (default `~/.cursor/skills`)

Before a PR that touches **`skills/**`**, **`docs/**`**, or **`.cursor/tests/**`**, run **`./.cursor/tests/run.sh`** (or **`./.cursor/scripts/run.sh`**).

## Public skill shape

Each **`@gh-*`** skill uses a fixed orchestration shape:

1. **`## Before batch`** — mandatory prep (**always run first**): peer **`@…`**, tooling, optional **`read-repo-stream`**
2. **`## Required internal skills`** — **`read-*` / `write-*`** libraries this skill depends on (names only)
3. Skill body → **`## Verification`**
4. **`## Recommended next steps`** — ranked follow-ups via [`read-skill-suggestions`](../skills/internal/read/skill-suggestions/SKILL.md) + [`read-safety-structured-qa` §9](../skills/internal/read/safety/structured-qa/SKILL.md) (one optional **AskQuestion**; not auto-orchestration)

## Standard GitHub flows

| Flow | Steps |
| --- | --- |
| **Discovery → issues** | chat/planning → `@gh-issue` → `@gh-issue-pick` |
| **Backlog → execute → PR** | `@gh-issue-backlog` / `@gh-issue-next` → `@gh-issue-execute` → `@gh-pr` → `@gh-pr-view` |
| **PR merge** | `@gh-pr-review` or `@gh-pr-view` → user merges in GitHub UI |
| **Issue → PR** | `@gh-issue-view` → implement (out of pack) → `@gh-pr` |
| **PR review (AI)** | `@gh-pr-review` or `@gh-pr-view` |
| **PR vs issue** | `@gh-pr-view` + `@gh-issue-view`; use `@gh-issue-review` when reshaping issue text |

Local branch creation, commit, push, and post-merge branch cleanup are **out of scope** for this pack — handle them in your editor, terminal, or other tooling before invoking **`@gh-pr`**.

## Delivery hand-off

1. Start from a tracked issue when possible (`@gh-issue-view` or `@gh-issue-next`).
2. Break scope into ordered checkpoints (chat or issue body).
3. Execute checkpoints with evidence (`@gh-issue-execute`).
4. Ensure head commits are on the remote, then **`@gh-pr`**; optional **`@gh-pr-review`** before merge in the UI.

## Repository improvement requirements

| Stage | Skill | Required input | Required output |
| --- | --- | --- | --- |
| Discover | chat/planning + `@gh-issue` | Goal + repo context | Deduped issues + labels + clear scope |
| Backlog inspect | `@gh-issue-backlog` | Open epic/child tree | Ordered themes + optional reorder proposal |
| Execute | `@gh-issue-execute` | Accepted checkpoints | Checkpoint status + verification evidence |
| PR create | `@gh-pr` | Published branch work | PR title/body aligned to issue intent |
| PR review | `@gh-pr-review` | PR id + optional issue context | Acceptance verdict + gaps/follow-ups |
| Merge | GitHub UI | Merge-ready decision | Merged PR (confirm via `@gh-pr-view`) |

If any stage output is missing, return to the prior stage instead of pushing forward.

## Model-tier guidance (optional)

| Phase | Typical model | Why |
| --- | --- | --- |
| Wording / issue polish | `composer-2` | Fast iteration on titles and acceptance criteria |
| Implementation + verify | `codex-5.3` | Multi-file changes and test runs |

## See also

- [`README.md`](../README.md) — install and skill picker
- [`gh.md`](gh.md) — full `@gh-*` catalog
- [`README.md`](README.md) — wiki hub and invoke graph
