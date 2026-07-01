# Read libraries (`skills/internal/read/**`)

Path-faithful naming rule: `skills/internal/read/<path>/SKILL.md` => `name: read-<path-with-dashes>`.

## Domain roots

| Domain | Read root |
| --- | --- |
| Workflow | [`skills/internal/read/workflow/git/SKILL.md`](../skills/internal/read/workflow/git/SKILL.md) |
| GitHub | [`skills/internal/read/repo/github/SKILL.md`](../skills/internal/read/repo/github/SKILL.md) |

**Related:** [Write libraries](write.md) · [Wiki hub](README.md) · [GitHub skills](gh.md)

## Notes

- Avoid repeated parent segments (`foo/foo`) in paths.
- Confirm / AskQuestion policy: [`read-safety-structured-qa`](../skills/internal/read/safety/structured-qa/SKILL.md), [`read-safety-skill-safety`](../skills/internal/read/safety/skill-safety/SKILL.md).
- Recommended next steps (public hand-off): [`read-skill-suggestions`](../skills/internal/read/skill-suggestions/SKILL.md).
- Mutations: [`docs/write.md`](write.md).

## Command ownership (`shuttle gh` / `shuttle git`)

Each subcommand family has **one** normative owner under `skills/internal/read/shuttle/**`. Legacy `read-issue-*` / `write-*` gh libs are **deprecated redirects** only. Other skills link to shuttle owners—no duplicate fenced recipes. CI: `.cursor/tests/check-read-write-command-ownership.py`, `.cursor/tests/check-shuttle-only-cli.py`.

| Command family | Owner |
| --- | --- |
| **`shuttle gh issue`** list / view / search | [`read-shuttle-gh-issue-read`](../skills/internal/read/shuttle/gh/issue-read/SKILL.md) |
| **`shuttle gh issue`** create / edit / close / delete / comment / batch | [`read-shuttle-gh-issue-commands`](../skills/internal/read/shuttle/gh/issue-commands/SKILL.md) |
| **`shuttle gh label`** list / sync / delete | [`read-shuttle-gh-label-read`](../skills/internal/read/shuttle/gh/label-read/SKILL.md) |
| **`shuttle gh pr`** list / view / diff | [`read-shuttle-gh-pr-read`](../skills/internal/read/shuttle/gh/pr-read/SKILL.md) |
| **`shuttle gh pr`** create / edit / close | [`read-shuttle-gh-pr-commands`](../skills/internal/read/shuttle/gh/pr-commands/SKILL.md) |
| **`shuttle gh repo`** view (templates, identity) | [`read-shuttle-gh-repo-read`](../skills/internal/read/shuttle/gh/repo-read/SKILL.md) |
| **`shuttle gh backlog`** tree / next / resequence | [`read-shuttle-gh`](../skills/internal/read/shuttle/gh/SKILL.md) (backlog section) |
| **`shuttle git`** read (branch, diff, log, remote, …) | [`read-shuttle-git`](../skills/internal/read/shuttle/git/SKILL.md) |
| Label heuristics (proposals, not fences) | [`read-issue-labels`](../skills/internal/read/issue/labels/SKILL.md) |
| PR delta narrative (local git via shuttle) | [`read-diff-summary`](../skills/internal/read/diff/summary/SKILL.md) |

**Implementation:** [shuttle-cli](https://github.com/gardusig/shuttle-cli) epic **01** ([#34](https://github.com/gardusig/shuttle-cli/issues/34)).

**Deprecated redirects (do not add new refs):** `read-issue-list`, `read-issue-view`, `read-pr-list`, `write-issue-commands`, `write-pr-commands`, `read-repo-forms-json`, `read-issue-labels-label-decorate`.
