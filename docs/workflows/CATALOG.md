# Workflow Catalog

`gardusig/cli` hosts reusable routers and hub-only images (`docker/operator.dockerfile`, `docker/cli-base.dockerfile`). Each app repo owns a root `Dockerfile` (or `docker/Dockerfile` for complex layouts).

## Pull Request

| Router | Target | App config |
|--------|--------|------------|
| `.github/workflows/pull-request.yml` | Reusable PR router | Called by every app repo on pull requests to `main` |

### Repos with PR pipelines

| Repo | Docker image | Typical stages |
|------|--------------|----------------|
| `gardusig/cli` | `Dockerfile` | lint → hygiene → version-check → core-gates → unit/integration |
| `gardusig/chrome-extensions` | `Dockerfile` | lint → hygiene → unit → build |
| `gardusig/database` | `Dockerfile` | lint → hygiene → validate → validate-tasks |
| `gardusig/gardusig` | `Dockerfile` | lint → hygiene |
| `gardusig/static-puzzles` | `Dockerfile` | lint → hygiene |
| `gardusig/animated-games` | `Dockerfile` | lint → hygiene |
| `gardusig/tex` | `docker/Dockerfile` | lint → hygiene → latex → Pages deploy |
| `gardusig/wiki` | `Dockerfile` (+ `docker/mermaid.Dockerfile`) | lint → hygiene → Mermaid validate |
| `gardusig/cli` | `Dockerfile` | lint → hygiene |
| `gardusig/cpp` | `Dockerfile` | lint → hygiene → compile → smoke |
| `gardusig/go` | `Dockerfile` | test |
| Language repos (`python`, `javascript`, …) | `Dockerfile` | lint → hygiene |

## Operations

| Workflow | Target | CLI entry |
|----------|--------|-----------|
| `.github/workflows/operator-test.yml` | Any app repo (selective) | `cli test packages resolve` / `run` |
| `.github/workflows/operator-craft-plan.yml` | Any app repo (issue plan) | `cli opencode gh issue --plan-only` |
| `.github/workflows/operator-craft-execute.yml` | Any app repo (issue execute) | `cli opencode gh execute` |
| `.github/workflows/operator-review.yml` | Any app repo (PR review) | `cli opencode gh review` |
| `.github/workflows/operator-dispatch.yml` | Operator lane router | `cli deploy operator` / `repository_dispatch` |
| `.github/workflows/project-recurrence.yml` | Recurrent board polling | `cli project recurrence check` |
| `.github/workflows/operator-runner-publish.yml` | `ghcr.io/gardusig/operator-runner` | Docker publish |
| `.github/workflows/tasks.yml` | `gardusig/database` | `cli tasks ...` |
| `.github/workflows/repo-review.yml` | Configured repo review jobs | Docker review targets |
| `.github/workflows/release.yml` | `gardusig/cli` release | Docker release targets |
| `.github/workflows/python-cli-main-release.yml` | `gardusig/cli` main release | Tag, PyPI publish, GitHub release, CLI base image build |
| `.github/workflows/python-cli-test-nightly.yml` | `gardusig/cli` | Nightly suite plan + core-gates + full unit/integration Docker legs |
| `.github/workflows/markdown.yml` | Any checked-out repo | Deprecated standalone Markdown/Mermaid gate |

## CLI Use

Workflows install the latest CLI release from PyPI:

```bash
pip install --no-cache-dir gardusig-cli
cli configure import-env
```

Set `CLI_PACKAGE=gardusig-cli==<version>` only when a workflow must pin a rollout.
