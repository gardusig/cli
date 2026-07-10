# CLI Workflow Catalog

CLI workflows are named operating procedures that use `gardusig/python-cli` as the integration layer. Pipeline-backed workflows live in `gardusig/cli`; app repos only provide code, data, and configuration.

## Scope

| Scope | Rule |
| --- | --- |
| Workflow host | `gardusig/cli` |
| Initial pipeline targets | `gardusig/database`, `gardusig/python-cli` |
| Future targets | Any non-pipeline repo with an explicit reviewed workflow entry |
| Excluded target | `gardusig/cli` |
| Local-only targets | Repos listed in local CLI config, such as `backup.repositories` |

Do not add a target workflow for the pipeline repo itself. It may host dispatch smoke tests and orchestration, but it is not treated as an app repo for CLI workflows.

## Definition Paths

Separate CLI workflow definitions should use a stable path per target repo:

| Target | Path pattern |
| --- | --- |
| `gardusig/database` | `.github/workflows/cli/private/<workflow>.yml` |
| `gardusig/python-cli` | `.github/workflows/cli/python-cli/<workflow>.yml` |
| Future app repo | `.github/workflows/cli/<repo-slug>/<workflow>.yml` |

Each workflow definition must declare:

- Target repo and checkout ref.
- CLI command sequence.
- Required secrets and GitHub environment.
- Write behavior, including destructive steps.
- Review or rollback expectation.
- Whether it is pipeline-backed, hybrid, or local-only documentation.

## Pipeline-Backed Workflows

| Workflow | Target | Command sequence |
| --- | --- | --- |
| `private-task-board-reset` | `gardusig/database` | `cli validate tasks` -> delete all issues -> insert all task issues -> reconcile Project membership -> update board order |
| `private-task-board-from-notion` | `gardusig/database` | `cli tasks ingest-pr --source notion --yes` -> PR review/merge -> optional `private-task-board-reset` |
| `private-notion-deploy` | `gardusig/database` | `cli tasks pairs build` -> `cli validate tasks` -> `cli notion deploy --yes` |
| `private-notion-cleanup` | `gardusig/database` | `cli notion cleanup --yes` |
| `private-notion-sync` | `gardusig/database` | `cli notion ingest` -> `cli notion deploy --yes` |
| `private-gh-issues-ingest-pr` | `gardusig/database` | `cli tasks ingest-pr --source github --yes` |
| `private-gh-issues-prune-closed` | `gardusig/database` | `cli gh issues prune --closed-older-than 7d --yes` |
| `python-cli-release-lane` | `gardusig/python-cli` | version check -> package build -> TestPyPI/PyPI validation -> tag/release publish |
| `python-cli-command-contract` | `gardusig/python-cli` | public command surface check -> docs link check -> dispatch smoke check |
| `chat-to-issues` | configured GitHub repos | distill chat/plan -> categorize by repo -> create/update epics and children -> organize backlog |
| `main-auto-tag-deploy` | repo with tag policy | readiness check -> no blocking PRs -> create/push next tag -> central release/deploy pipeline |

## Hybrid Workflows

Hybrid workflows start locally through CLI and rely on central CI or GitHub review for verification:

| Workflow | Scope | Sequence |
| --- | --- | --- |
| `issue-ship-manual` | Any GitHub repo | `cli gh backlog next` -> `cli git reset --yes --main-only` -> `cli git start ... --yes` -> work/push -> `cli git review` -> `cli gh pr create ... --yes` -> GitHub UI merge -> `cli git reset --yes --delete-merged` |
| `ai-issue-ship` | Any GitHub repo with AI config | `cli opencode gh next` -> branch prep -> `cli opencode gh execute ... --pr --yes` -> `cli opencode gh review ... --yes` -> GitHub UI merge |
| `plan-to-issues` | Any GitHub repo | `cli gh label sync ... --yes` -> `cli gh issue batch --file plan.yaml --yes` -> `cli gh backlog tree --format json` -> `cli gh backlog next --format json` |
| `repo-health-verify` | Any configured repo | `cli git review` -> unit/integration checks -> command surface checks -> optional Docker verification |
| `pipeline-dispatch-smoke` | Dispatch payloads only | `cli pipeline run ... --dry-run` against known workflow targets |

## Local-Only Workflows

Local-only workflows are cataloged because they use the same CLI integration surface, but they should not get pipeline workflow files without a separate secrets/OAuth decision.

| Workflow | Scope | Sequence |
| --- | --- | --- |
| `tag-backup-cloud` | Current git repo | `cli git tag --yes` -> `cli git zip` -> `cli drive upload` |
| `multi-repo-drive-sync` | `backup.repositories` | `cli drive ingest` -> `cli drive status` -> `cli drive deploy` |
| `chrome-bookmarks-roundtrip` | Local Chrome config | `cli chrome bookmarks ingest` -> edit local file -> `cli chrome bookmarks deploy` |
| `workspace-reset-after-merge` | Current git repo | GitHub UI merge -> `cli git reset --yes --delete-merged` |
| `docker-reset-verify` | Local Docker host | `cli docker reset --yes` -> `cli test integration` |
| `config-bootstrap-tasks` | Local CLI config | `cli config init` -> `cli config secrets init` -> set Notion/GitHub targets -> `cli config check --tasks` |

## GitHub Projects Boundary

General-purpose `cli gh project ...` remains blocked for ad hoc terminal use. The only planned Project integration is through named task board workflows, where the reviewed sequence can add deployed issues to the configured Project and update board order.
