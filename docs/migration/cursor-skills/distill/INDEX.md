# cursor-skills → cli port index

Embedded from `gardusig/cursor-skills` (see `../MANIFEST.json` for commit SHA).

**Status:** All public `@gh-*` skills are implemented as `cli gh` / `cli craft` / `cli review` commands. See [docs/craft.md](../../../../craft.md).

## Public `@gh-*` skills (16)

| cursor-skills skill | Snapshot path | cli target | Status |
|---------------------|---------------|------------|--------|
| `@gh-issue-list` | `snapshot/skills/gh/issue/list/SKILL.md` | `cli gh issue list` | done |
| `@gh-issue-view` | `snapshot/skills/gh/issue/view/SKILL.md` | `cli gh issue context` | done |
| `@gh-issue` | `snapshot/skills/gh/issue/SKILL.md` | `cli craft issue` | done |
| `@gh-issue-pick` | `snapshot/skills/gh/issue/pick/SKILL.md` | `cli craft pick` | done |
| `@gh-issue-backlog` | `snapshot/skills/gh/issue/backlog/SKILL.md` | `cli gh backlog tree` | done |
| `@gh-issue-next` | `snapshot/skills/gh/issue/next/SKILL.md` | `cli craft next` | done |
| `@gh-issue-labels` | `snapshot/skills/gh/issue/labels/SKILL.md` | `cli gh label sync` | done |
| `@gh-issue-review` | `snapshot/skills/gh/issue/review/SKILL.md` | `cli craft issue --review` | done |
| `@gh-issue-execute` | `snapshot/skills/gh/issue/execute/SKILL.md` | `cli craft execute` | done |
| `@gh-issue-close` | `snapshot/skills/gh/issue/close/SKILL.md` | `cli gh issue close` | done |
| `@gh-issue-delete-closed` | `snapshot/skills/gh/issue/delete/closed/SKILL.md` | `cli gh issue delete` | done |
| `@gh-pr-list` | `snapshot/skills/gh/pr/list/SKILL.md` | `cli gh pr list` | done |
| `@gh-pr-view` | `snapshot/skills/gh/pr/view/SKILL.md` | `cli gh pr view` | done |
| `@gh-pr` | `snapshot/skills/gh/pr/SKILL.md` | `cli craft pr` | done |
| `@gh-pr-review` | `snapshot/skills/gh/pr/review/SKILL.md` | `cli review pr` | done |
| `@gh-pr-close` | `snapshot/skills/gh/pr/close/SKILL.md` | `cli gh pr close` | done |

**Excluded:** `gh pr merge` — UI-only per cli merge policy.

## Internal libraries (high value)

| Library | Snapshot path | cli destination | Status |
|---------|---------------|-----------------|--------|
| shuttle gh map | `snapshot/skills/internal/read/shuttle/gh/SKILL.md` | `src/services/gh_service.py` | done |
| workflow lanes | `distill/workflows-lanes.md` | `docs/workflows.md` | done |
| structured Q&A | `distill/safety-write-gate.md` | `src/internal/write/gate.py` | done |
| skill safety | `snapshot/skills/internal/read/safety/skill-safety/SKILL.md` | `src/internal/read/safety.py` | done |
| issue dedupe | `snapshot/skills/internal/read/issue/dedupe/SKILL.md` | `src/services/issue_craft.py` | done |
| issue nesting | `snapshot/skills/internal/read/issue/nesting/SKILL.md` | `cli gh issue batch` | done |
| PR orchestration | `snapshot/skills/internal/read/pr/content/pr-orchestration/SKILL.md` | `src/services/pr_craft.py` | done |
| PR preflight | `snapshot/skills/internal/read/pr/preflight-qa/SKILL.md` | `cli git review` | done |
| pack tests | `snapshot/tests/` | `tests/pack/` | done |

## Dropped (in snapshot only)

- `snapshot/skills/internal/read/docs/*` (28 skills) — doc-authoring scaffolds
- Deprecated `write/issue/commands`, `write/pr/commands` redirects

## AI stack

| Layer | Path |
|-------|------|
| DeepSeek 3 roles | `config/deepseek/models.yaml`, `src/providers/deepseek.py` |
| OpenCode wrapper | `src/providers/opencode.py` |
| Craft prompts | `src/services/craft_ai.py` |
| Issue flows | `src/services/issue_craft.py` |
| PR flows | `src/services/pr_craft.py` |
