# Workflow Catalog

Workflows live in this repository. App repos own a thin `.github/workflows/pull-request.yml` that calls the PR router here on pull requests to `main`.

| Family | Router | Repo configs |
| --- | --- | --- |
| Pull request | `.github/workflows/pull-request.yml` (`workflow_call` + dispatch) | `.github/workflows/pull-request/*.yaml` |
| Markdown validation | `.github/workflows/markdown.yml` | Deprecated standalone docs gate; normal PR lint uses `cli lint repo` |
| Release | `.github/workflows/release.yml` | `.github/workflows/release/*.yaml` |
| Tasks | `.github/workflows/tasks.yml` | `.github/workflows/tasks/database.yaml` |
| Repo review | `.github/workflows/repo-review.yml` | `.github/workflows/repo-review/*.yaml` |
| CLI workflows | `.github/workflows/cli/<repo>/<workflow>.yml` | Separate named workflow definitions per CLI workflow |
| Markdown Docker gate | `docker/markdown.dockerfile` | Deprecated standalone helper; repo Dockerfiles own the `lint` stage |

See:

- `docs/workflows/pull-request-events.md`
- `docs/workflows/database.md`
- `docs/workflows/python-cli.md`
- `docs/workflows/cli.md`
- `docs/workflows/markdown.md`
- `docs/workflows/chrome-extensions.md`
- `docs/workflows/tex.md`
- `docs/secrets.md`

## CLI Workflow Targets

CLI workflows are cataloged separately from PR/release/review routers. They use `gardusig/python-cli` as the integration layer and `gardusig/cli` as the workflow host.

| Target repo | Definition namespace | Notes |
| --- | --- | --- |
| `gardusig/database` | `.github/workflows/cli/private/*.yml` | Task board, Notion, GitHub Issues, and Project/order workflows |
| `gardusig/python-cli` | `.github/workflows/cli/python-cli/*.yml` | CLI release, command contract, and dispatch smoke workflows |
| Future app repos | `.github/workflows/cli/<repo-slug>/*.yml` | Allowed only after a reviewed explicit workflow entry |

`gardusig/cli` is excluded as a target repo. It may host orchestration and smoke checks, but app-style CLI workflows must not target the pipeline repo itself.

## Per-Repo Examples

| Repo | Specific workflow example |
| --- | --- |
| `database` | `repo-lint` -> `validate`; `cli/private/database-task-board-reset.yml`; `tasks.yml` -> `github-deploy` / `notion-deploy`; `repo-review.yml` -> `validate-tasks` |
| `python-cli` | `repo-lint` -> `unit-test`; `cli/python-cli/python-cli-release-lane.yml`; `repo-review.yml` -> `version-check`, `command-surface` |
| `chrome-extensions` | `repo-lint` -> `unit-test` -> `build`; `repo-review.yml` -> `unit-test`, `build` |
| `tex` | `repo-lint` -> `repo-hygiene` -> `latex`; `repo-review.yml` -> `lint`, `latex` |
