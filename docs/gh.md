# GitHub integration (`cli gh`)

Deterministic GitHub operations for agents and humans. Uses authenticated **`gh`** by default, with an API token fallback for issue/PR REST operations and full Projects v2 GraphQL when `--transport api` or `auto` selects the API path. Output is JSON-first and writes use the same write-gate model as `cli git`.

**AI orchestration:** [opencode.md](opencode.md) — `cli opencode gh` for AI-assisted issues/PRs; `cli gh` for deterministic GitHub I/O.

## Prerequisites

- `gh` installed and authenticated (`gh auth status`), or `GITHUB_TOKEN` / `GH_TOKEN` for API transport
- `cli` on PATH

## Global flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `--repo owner/name` | gh context | Target repository |
| `--format json\|table` | `json` | Output shape (agents use json) |
| `--transport cli\|api\|auto` | `auto` | Prefer authenticated `gh`; fall back to API token in `auto` |
| `--yes` / `-y` | off | Skip interactive write gate (use after Cursor **Proceed**) |

Transport rules:

- `cli`: force subprocess `gh` behavior.
- `api`: use GitHub REST/GraphQL adapters; requires `--repo owner/name` or configured `gh.issues.repo` for repo-scoped operations.
- `auto`: use authenticated `gh` when available, otherwise use `GITHUB_TOKEN`, `GH_TOKEN`, or `auth.gh.token_file`.

When neither authenticated `gh` nor a token is available, `auto` and `api` fail with a single actionable error: *GitHub API transport needs GITHUB_TOKEN, GH_TOKEN, or auth.gh.token_file.*

### Transport selection

| Context | Recommended transport |
| --- | --- |
| Local dev with `gh auth login` | `auto` (default) |
| CI / headless agents with PAT | `api` + `--repo owner/name` |
| Debugging CLI vs API drift | force `cli` or `api` explicitly |

### Token scopes

API transport needs a GitHub token with scopes matching the operation:

| Surface | Classic PAT scopes | Fine-grained equivalent |
| --- | --- | --- |
| Issues, PRs, labels, repo reads | `repo` | Repository: Issues, Pull requests, Contents (read); Metadata |
| Projects v2 (`cli gh project`) | `repo`, `project` | Repository + Projects (read/write) |
| Org-owned projects | above + org membership | Organization project permissions |

Configure via `GITHUB_TOKEN`, `GH_TOKEN`, or `auth.gh.token_file` in config.

### Transport parity

Every **shipped** command below works on both transports unless noted. This table is the acceptance checklist for Epic 11 (#69); `tests/gh/test_transport.py` parametrizes the P0 issue/PR API rows.

#### Issues

| Command | CLI | API | Policy / notes |
| --- | --- | --- | --- |
| `issue list` | yes | yes | REST |
| `issue view` | yes | yes | REST; `--comments` supported |
| `issue search` | yes | yes | REST search |
| `issue create` | yes | yes | REST |
| `issue edit` | yes | yes | REST |
| `issue reopen` | yes | yes | REST |
| `issue delete` | yes | yes | REST |
| `issue comment` | yes | yes | REST |
| `issue status` | yes | CLI | uses `gh` status aggregate |
| `issue context` | yes | yes | composed REST (`issue view` + `list` + body `#N` refs) |
| `issue batch` | yes | CLI-only | YAML batch orchestration |
| `issue close` | blocked | blocked | policy — merge PR with Fixes/Closes |

#### Pull requests

| Command | CLI | API | Policy / notes |
| --- | --- | --- | --- |
| `pr list` | yes | yes | REST |
| `pr view` | yes | yes | REST |
| `pr diff` | yes | yes | REST files API (`--stat`) or diff URL |
| `pr create` | yes | yes | REST |
| `pr edit` | yes | yes | REST |
| `pr comment` | yes | yes | REST |
| `pr close` | yes | yes | REST |
| `pr reopen` | yes | yes | REST |
| `pr checks` | yes | yes | REST check-runs |
| `pr review` | yes | yes | REST |
| `pr ready` | yes | yes | REST GraphQL mutation via transport |
| `pr status` | yes | CLI | uses `gh` status aggregate |
| `pr` (shortcut) | yes | yes | API path uses REST + Contents API for `--template` |
| `pr merge` | blocked | blocked | policy — use GitHub UI / auto-merge |

#### Labels

| Command | CLI | API | Policy / notes |
| --- | --- | --- | --- |
| `label list` | yes | yes | REST |
| `label create` | yes | yes | REST |
| `label delete` | yes | yes | REST |
| `label sync` | yes | CLI | manifest diff + subprocess |

#### Projects (`cli gh project`)

| Command | CLI | API | Policy / notes |
| --- | --- | --- | --- |
| `project list` | yes | yes | GraphQL `projectsV2` |
| `project view` | yes | yes | GraphQL `projectV2` node |
| `project create` | yes | yes | GraphQL `createProjectV2` |
| `project edit` | yes | yes | GraphQL `updateProjectV2` |
| `project delete` | yes | yes | GraphQL `deleteProjectV2` |
| `project item list` | yes | yes | GraphQL items pagination |
| `project item view` | yes | yes | GraphQL item node |
| `project item add` | yes | yes | GraphQL `addProjectV2ItemById` |
| `project item edit` | yes | yes | GraphQL `updateProjectV2ItemFieldValue` |
| `project item delete` | yes | yes | GraphQL `deleteProjectV2Item` |

`--transport api` selects the GraphQL project provider; `--transport cli` uses `gh project` subprocess.

#### Repo & backlog (CLI-first)

| Command | CLI | API | Policy / notes |
| --- | --- | --- | --- |
| `repo view` | yes | partial | API: `pullRequestTemplates` via Contents API |
| `repo list` | yes | yes | REST |
| `repo readme-sync` | yes | CLI | write path via subprocess |
| `backlog *` | yes | CLI-only | label/topo logic over `gh` reads |

#### Boundary with Epic 08

- **`cli gh project`** — low-level GitHub Projects v2 CRUD hub; honors `--transport`.
- **`cli project`** — product workflow (pairs, lanes, deploy/ingest/sync, recurrence). See [project.md](project.md). Top-level `cli project` uses default `auto` transport unless extended.

## Double-gate contract

| Context | Cursor skill | cli write |
| --- | --- | --- |
| Agent after **Proceed** | AskQuestion in chat | append **`--yes`** |
| Human in terminal | — | interactive gate or **`--yes`** |
| Read-only | no gate | no **`--yes`** |

## Issue commands

### Read (no gate)

```bash
cli gh issue list --state open --limit 30 --format json
cli gh issue view 42 --format json
cli gh issue context 42 --format json
cli gh issue search "label:bug" --format json
```

### Write (gate unless `--yes`)

```bash
cli gh issue create --title "1 — Epic" --body-file body.md --label epic:foo --yes
cli gh issue edit 42 --title "1.1 — Child" --yes
cli gh issue reopen 42 --yes
cli gh issue delete 42 --yes
cli gh issue comment 42 --body "Note" --yes
cli gh issue status --format json
cli gh issue batch --file batch.yaml --yes
# cli gh issue close — blocked by policy (merge PR in UI and auto-close)
```

### Batch YAML shape

```yaml
operations:
  - action: create
    title: "1 — Epic title"
    body_file: .cursor/gh/issue/epic.md
    labels: ["epic:slug", "issue-type:epic"]
  - action: create
    title: "1.1 — Subissue"
    body_file: .cursor/gh/issue/subissue.md
    labels: ["epic:slug", "issue-type:child"]
  - action: edit
    number: 100
    body_file: .cursor/gh/issue/epic-updated.md
```

### Issue context (agent rollup)

`cli gh issue context N` returns one JSON object with the issue view, comments, epic issue/subissue context (from `epic:*` + `issue-type:*` labels), and `#N` body references resolved from the repo.

```bash
cli gh issue context 42 --format json
```

### Plan → backlog chain

```bash
cli gh issue batch --file plan.yaml --yes
cli gh backlog tree --format json
cli gh backlog next --format json
```

## Label commands

Manifest path: **`config/gh/labels.manifest.yaml`** (repo-owned epic/area taxonomy).

```bash
cli gh label list --format json
cli gh label create my-label --color ff0000 --yes
cli gh label delete my-label --yes
cli gh label sync --manifest config/gh/labels.manifest.yaml --yes
cli gh label sync --manifest config/gh/labels.manifest.yaml --prune-orphans --yes
```

Retro-label open issues from a batch file:

```bash
cli gh issue batch --file config/gh/backlog-labelize.batch.yaml --yes
```

Common command map:

| Flow | CLI |
| --- | --- |
| Backlog | `cli gh backlog next`, `cli gh backlog tree` |
| Issues | `cli gh issue list`, `cli gh issue view`, `cli gh issue create`, `cli gh issue edit`, `cli gh issue reopen`, `cli gh issue status`, `cli gh issue delete` |
| Labels | `cli gh label list`, `cli gh label sync` |
| Pull requests | `cli gh pr list`, `cli gh pr view`, `cli gh pr create`, `cli gh pr edit`, `cli gh pr checks`, `cli gh pr review`, `cli gh pr ready`, `cli gh pr close` |
| Projects | `cli gh project list`, `cli gh project create`, `cli gh project item add`, `cli gh project item edit` |
| Blocked by policy | `cli gh pr merge`, `cli gh issue close`, `cli gh ruleset` |

Full table: `cli links`.

## Pull request commands

```bash
cli gh pr list --format json
cli gh pr view 10 --format json
cli gh pr diff 10
cli gh pr --yes                         # push if needed, then open PR titled "."
cli gh pr --template bugfix --yes       # use an explicit PR template
cli gh pr --no-push --yes               # create only when branch is already published
cli gh pr create --title "…" --body-file pr.md --yes
cli gh pr edit 10 --body-file pr.md --yes
cli gh pr comment 10 --body "Looks good" --yes
cli gh pr checks 10 --format json
cli gh pr review 10 --approve --body "Approved" --yes
cli gh pr ready 10 --yes
cli gh pr reopen 10 --yes
cli gh pr status --format json
cli gh pr close 10 --yes
# cli gh pr merge — blocked by policy (use GitHub UI / auto-merge)
# cli gh issue close — blocked by policy (merge PR in UI and auto-close)
# cli gh ruleset … — blocked by policy (use GitHub UI)
```

`cli gh pr` without a subcommand is the quick PR shortcut. It uses title `.`,
an empty body by default, runs the same write-gated push path as `cli git push`
when the branch is dirty or unpublished, and then creates the PR. Use
`--template NAME` to opt into a repository PR template; templates are not applied
implicitly. When an open PR already exists for the branch, the shortcut returns
that PR (`existing: true` in JSON) instead of creating a duplicate.

## Project commands {#projects}

GitHub Projects v2 CRUD is available through `cli gh project ...`; write commands use the same gate as issue and PR commands. `cli gh project` is the low-level transport/CRUD surface. `cli project` remains the product workflow for recurrent boards, lanes, local task pairs, deploy/ingest/sync, and recurrence.

```bash
cli gh project list --owner gardusig --format json
cli gh project view 1 --owner gardusig --format json
cli gh --transport api project view 1 --owner gardusig --format json  # GraphQL Project v2 node
cli gh project create --owner gardusig --title "Roadmap" --yes
cli gh project edit 1 --owner gardusig --title "Roadmap v2" --yes
cli gh project delete 1 --owner gardusig --yes

cli gh project item list 1 --owner gardusig --format json
cli gh project item view --project 1 --owner gardusig --id ITEM_ID
cli gh project item add --project 1 --owner gardusig --issue 42 --lane todo --yes
cli gh project item edit --project 1 --owner gardusig --id ITEM_ID --field Status --value Done --kind single-select --yes
cli gh project item delete --project 1 --owner gardusig --id ITEM_ID --yes
```

## Blocked commands {#blocked-commands}

Some GitHub surfaces are **registered in the CLI** (they appear in `cli gh --help`) but **always exit with a policy error**.

| Blocked | CLI | Use instead |
| --- | --- | --- |
| PR merge | `cli gh pr merge N` | GitHub UI or PR **auto-merge** |
| Issue close | `cli gh issue close N` | Merge a PR in GitHub UI with `Fixes #N`, `Closes #N`, or `Resolves #N` |
| Rulesets | `cli gh ruleset …` | GitHub repository/org settings UI |

List programmatically:

```bash
cli gh policy list --format json
```

**Provider guard:** any code path that calls `GhProvider.run()` with matching `gh` argv is rejected before subprocess spawn (same messages). PR merge has break-glass only: `CLI_ALLOW_GH_MERGE=1` (not recommended). Issue close has no break-glass.

## Issue/Subissue Backlog

Epic issues and subissues are organized with labels and ordinary GitHub issue references:

```bash
cli gh backlog organize --format json   # epic issues -> subissues (step 1..N)
cli gh backlog levels --format json     # priority:1..N explanations
cli gh backlog next --format json
```

`cli project ...` remains available for higher-level board workflows built on the same Projects provider.

## Repo commands

```bash
cli gh --format json repo view
cli gh --format json repo view --json-fields nameWithOwner,owner,issueTemplates,pullRequestTemplates
cli gh --format json repo list --owner gardusig
cli gh repo readme-sync --readme README.md --owner gardusig --dry-run
```

## Backlog commands

Epic issue/subissue organization uses **`issue-type:epic`**, **`issue-type:child`**, **`epic:<slug>`**, and **`priority:N`** labels (levels 1–5; see `config/gh/priority-levels.yaml`). Subissue titles use **`{step} — {name}`** (step = topological order within the epic issue).

```bash
cli gh backlog organize --format json   # epic issues + sorted subissues + readiness
cli gh backlog levels --format json     # priority scale with explanations
cli gh backlog tree --format json       # same tree as organize (legacy keys included)
cli gh backlog next --format json
cli gh backlog resequence --file plan.yaml --yes
```

### Pick next issue workflow

Use `cli gh` for deterministic issue selection and context gathering. It does not call AI
providers or spend API tokens beyond normal GitHub `gh` reads.

```bash
cli gh --repo gardusig/python-cli backlog next --format json
cli gh --repo gardusig/python-cli issue context 81 --format json
cli test packages resolve --changed-path src/commands/gh.py --format json
```

If the selected issue needs AI planning, hand off explicitly to `cli opencode gh` after
reviewing the context. Keep implementation and test selection decisions reproducible in
`cli gh` and `cli test packages`.

Resequence plan YAML:

```yaml
renames:
  - number: 42
    title: "1.2 — Renamed subissue"
```

## JSON output examples

**`backlog next`:**

```json
{
  "number": 71,
  "title": "1.1 — PR prevalidate",
  "url": "https://github.com/owner/repo/issues/71",
  "sequence": "1.1 —"
}
```

**`backlog tree`:**

```json
{
  "repo": "owner/repo",
  "roots": [{"number": 70, "title": "1 — Epic", "sequence": "1 —"}],
  "epics": {"epic:slug": [{"number": 71, "title": "1.1 — Child"}]}
}
```

## Epic 11 closure (PR #88)

Parent [#69](https://github.com/gardusig/python-cli/issues/69). Close when PR #88 merges and
verification below is green.

| Slice | Shipped evidence |
| --- | --- |
| Transport refactor | `GhTransport` CLI/API/auto — [`src/providers/gh_transport.py`](../src/providers/gh_transport.py); `--transport` on `cli gh` |
| Issue/PR P0–P1 CRUD | `issue reopen`, `pr comment/reopen/checks/review/ready` — § Transport parity; `tests/gh/test_transport.py` |
| `issue context` API | Composed REST — `tests/gh/test_issue_context.py`; `gh issue context api` in `cli_api_checks.py` |
| Projects GraphQL | All `cli gh project` commands on API transport — `tests/gh/test_commands.py`; `gh project view api` / `item add api` checks |
| `cli gh pr` shortcut | Push-first PR — `tests/gh/test_pr_shortcut.py`; `gh pr shortcut api` transport smoke |
| Operator headless lane | `--transport api` in [hub-operator.md](hub-operator.md) ship lane |
| Docs + integration | This § Transport parity table; API smoke in [`cli_api_checks.py`](../src/integration/cli_api_checks.py) |

**CLI-only by design:** `issue batch`, `label sync`, `backlog *`, `issue status`, `pr status`, `repo readme-sync`.

```bash
uv run pytest tests/gh/test_transport.py tests/gh/test_issue_context.py tests/pack/test_gh_hub_epic.py -q
uv run pytest tests/cli/test_api_integration.py -q
uv run python tests/integration/check_integration_coverage.py
```

## Tests

Unit tests mock the gh provider: `tests/gh/test_commands.py`.

Run: `cli test python unit .`

## See also

- [architecture.md](architecture.md) — CLI → Service → Provider
- [opencode.md](opencode.md) — AI entry point (`cli opencode`)
- cli epic **01** — GitHub integration
