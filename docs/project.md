# GitHub Projects

`cli project` is the supported GitHub Projects v2 surface. Raw `cli gh project ...`
commands remain blocked by policy so board writes happen through named,
write-gated workflows.

## Configuration

Project defaults live in `config/config.yaml` or an override loaded through
`CLI_BOARD_FILE`:

```yaml
project:
  default:
    owner: gardusig
    number: 1
  auto_link:
    enabled: true
    default_lane: todo
    on_issue_create: true
  fields:
    status: Status
    deadline: Deadline
    type: Type
  lanes:
    backlog: Backlog
    todo: Todo
    doing: In Progress
    review: In review
    done: Done
  task_root: config/project
  pairs_file: tasks.pairs.json
```

`project.lanes` maps friendly CLI names to exact single-select option labels on
the board. `project.fields` maps stable CLI concepts to project field names.

## Read Commands

```bash
cli project list --owner gardusig --format json
cli project view 1 --owner gardusig --format json
cli project field list 1 --owner gardusig --format json
cli project item list --format json
cli project item view --id PVTI_x --format json
```

## Board Writes

Mutating commands require `--yes` outside an interactive terminal.

```bash
cli project item add --issue 42 --lane todo --yes
cli project item status --issue 42 doing --yes
cli project item set --issue 42 --field Deadline --value 2026-07-12 --kind date --yes
cli project item archive --issue 42 --yes
cli project item remove --issue 42 --delete --yes
```

Day-to-day aliases wrap the same service:

```bash
cli project link --issue 42 --lane todo --yes
cli project lane --issue 42 doing --yes
cli project unlink --issue 42 --yes
```

## Batch Spawn

`cli project spawn` creates issues from YAML and adds each one to the configured
project:

```bash
cli project spawn --file config/project/examples/seed.yaml --dry-run
cli project spawn --file config/project/examples/seed.yaml --yes
```

The manifest shape is:

```yaml
owner: gardusig
project: 1
status: Backlog
items:
  - title: "docs: weekly review"
    body_file: docs-weekly.md
    labels: [maintenance, recurrence:docs-weekly]
    status: Todo
```

## Local Pairs

Project pairs mirror the Notion header/body pattern:

```text
config/project/
  header/docs-weekly.yaml
  body/docs-weekly.yaml
  tasks.pairs.json
```

Build and inspect the manifest:

```bash
cli project pairs build
cli project pairs status
```

Deploy local headers and bodies to GitHub, ingest board state back to headers,
or run both:

```bash
cli project deploy --yes
cli project ingest
cli project sync --yes
```

`deploy` sorts **maintenance** and **tech-debt** pairs before feature work, then
creates or updates GitHub issues and board items for each enabled pair. When one
pair fails (for example API rate limits), deploy continues with the rest and
exits non-zero after printing `failed <name>: <error>` lines.

`ingest` is read-only: it matches manifest pairs to board items and writes
`forced_status`, `deadline`, `labels`, `issue_number`, and `item_id` back into
local header yaml from the project item and linked issue.

Maintenance and tech-debt pairs must provide either `deadline` or `interval`.
Feature pairs do not require deadlines by default. Disabled pairs
(`enabled: false`) are skipped on deploy.

## Recurrence

After a linked maintenance PR merges and the issue is closed, advance the next
cycle explicitly:

```bash
cli project recurrence advance --yes
cli project recurrence check --yes   # alias for advance (polling workflows)
```

The command creates a fresh issue from the local pair, sets the next deadline
from `interval` (default 7 days), and records the previous issue number in the
header. Re-copying the issue is preferred over reopening a closed card.

Hub polling: `gardusig/github-pipelines` → `.github/workflows/project-recurrence.yml`
(Mondays 09:00 UTC or manual `workflow_dispatch`).

```bash
gh workflow run project-recurrence.yml -R gardusig/github-pipelines \
  -f repository=gardusig/python-cli \
  -f ref=main
```

## Epic 08 closure (PR #88)

Parent [#66](https://github.com/gardusig/python-cli/issues/66). Close children when PR #88 merges and
verification below is green.

| Child | Issue | Shipped evidence |
| --- | --- | --- |
| 08.1 — foundation + read | [#72](https://github.com/gardusig/python-cli/issues/72) | `cli project list/view`, `field list`, `item list/view` — `docs/project.md` § Read Commands; `tests/project/test_project_service.py` |
| 08.2 — board write | [#73](https://github.com/gardusig/python-cli/issues/73) | `item add/status/set`, `link`, `lane`, `unlink` — § Board Writes; `project_integration.py` ok/refuse rows |
| 08.3 — batch spawn YAML | [#74](https://github.com/gardusig/python-cli/issues/74) | `cli project spawn` — § Batch Spawn; `config/project/examples/seed.yaml`; integration `project spawn dry-run` |
| 08.4 — auto-link + lane | [#75](https://github.com/gardusig/python-cli/issues/75) | `project.auto_link` in config; `gh issue create` links board — `tests/cli/test_project_command.py::test_gh_issue_create_auto_links_when_configured` |

Hub workflow: [github-pipelines `project-recurrence.yml`](https://github.com/gardusig/github-pipelines/blob/main/.github/workflows/project-recurrence.yml) ([PR #16](https://github.com/gardusig/github-pipelines/pull/16)).

```bash
uv run pytest tests/project/ tests/pack/test_project_epic.py tests/cli/test_project_command.py -q
uv run python tests/integration/check_integration_coverage.py
```
