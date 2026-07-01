# cursor-skills → cli port index

Embedded from `gardusig/cursor-skills` (see `../MANIFEST.json` for commit SHA).

## Public `@gh-*` skills (16)

| cursor-skills skill | Snapshot path | cli target | Status |
|---------------------|---------------|------------|--------|
| `@gh-issue-list` | `snapshot/skills/gh/issue/list/SKILL.md` | `cli gh issue list` | done |
| `@gh-issue-view` | `snapshot/skills/gh/issue/view/SKILL.md` | `cli gh issue context` | done |
| `@gh-issue` | `snapshot/skills/gh/issue/SKILL.md` | `cli craft issue` | pending |
| `@gh-issue-pick` | `snapshot/skills/gh/issue/pick/SKILL.md` | `cli craft issue --number N` | pending |
| `@gh-issue-backlog` | `snapshot/skills/gh/issue/backlog/SKILL.md` | `cli gh backlog tree` | done |
| `@gh-issue-next` | `snapshot/skills/gh/issue/next/SKILL.md` | `cli gh backlog next` | pending (topo sort) |
| `@gh-issue-labels` | `snapshot/skills/gh/issue/labels/SKILL.md` | `cli gh label sync` | done |
| `@gh-issue-review` | `snapshot/skills/gh/issue/review/SKILL.md` | `cli craft issue --review` | pending |
| `@gh-issue-execute` | `snapshot/skills/gh/issue/execute/SKILL.md` | `cli craft pr` + OpenCode | pending |
| `@gh-issue-close` | `snapshot/skills/gh/issue/close/SKILL.md` | `cli gh issue close` | done |
| `@gh-issue-delete-closed` | `snapshot/skills/gh/issue/delete/closed/SKILL.md` | `cli gh issue delete` | done |
| `@gh-pr-list` | `snapshot/skills/gh/pr/list/SKILL.md` | `cli gh pr list` | done |
| `@gh-pr-view` | `snapshot/skills/gh/pr/view/SKILL.md` | `cli gh pr view` | done |
| `@gh-pr` | `snapshot/skills/gh/pr/SKILL.md` | `cli craft pr` | pending |
| `@gh-pr-review` | `snapshot/skills/gh/pr/review/SKILL.md` | `cli review pr` | pending |
| `@gh-pr-close` | `snapshot/skills/gh/pr/close/SKILL.md` | `cli gh pr close` | done |

**Excluded:** `gh pr merge` — UI-only per cli merge policy.

## Internal libraries (high value)

| Library | Snapshot path | cli destination |
|---------|---------------|-----------------|
| shuttle gh map | `snapshot/skills/internal/read/shuttle/gh/SKILL.md` | `src/services/gh_service.py` |
| workflow lanes | `distill/workflows-lanes.md` | `docs/workflows.md` |
| structured Q&A | `distill/safety-write-gate.md` | `src/internal/write/gate.py` |
| skill safety | `snapshot/skills/internal/read/safety/skill-safety/SKILL.md` | `src/internal/read/safety.py` |
| issue dedupe | `snapshot/skills/internal/read/issue/dedupe/SKILL.md` | `cli craft issue` |
| issue nesting | `snapshot/skills/internal/read/issue/nesting/SKILL.md` | `cli gh issue batch` |
| PR orchestration | `snapshot/skills/internal/read/pr/content/pr-orchestration/SKILL.md` | `cli craft pr` |
| PR preflight | `snapshot/skills/internal/read/pr/preflight-qa/SKILL.md` | `cli git review` |
| pack tests | `snapshot/tests/` | `tests/pack/` (port) |

## Dropped (in snapshot only)

- `snapshot/skills/internal/read/docs/*` (28 skills) — doc-authoring scaffolds
- Deprecated `write/issue/commands`, `write/pr/commands` redirects
