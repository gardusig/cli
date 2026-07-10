# Workflow library

Reusable GitHub Actions workflows (formerly `gardusig/yaml`) plus this repo's publish pipelines.

## Hub routers

| Path | Purpose |
| --- | --- |
| `lib/` | `workflow_call` routers and shared lanes |
| `pull-request/` | Per-language PR gate configs |
| `dispatch.yml` | Manual router across catalog entries |
| `../config/ci/catalog.yaml` | Workflow registry |

App repos call `gardusig/cli/.github/workflows/lib/pull-request-router.yml@main`.

## This repo (`gardusig/cli`)

Three workflows — each maps to one stage of the publish path. Workflows run `docker build` against `.github/Dockerfile` or `.github/images/cli-runtime.Dockerfile`; commands live in `scripts/ci/*.sh`.

| File | Trigger | Purpose |
| --- | --- | --- |
| `pull-request.yaml` | PR → `main` | Version → unit → TestPyPI → install + integration |
| `main.yaml` | Push `main` | Publish to PyPI + consumer smoke |
| `release.yaml` | Tag `v*` | Runtime Docker image (PyPI install only) → Hub → pull smoke → GitHub release |

PR stage `pr` chains `version-check.sh`, `unit-test.sh`, and `pypi-test.sh` in one image build (local shortcut).

Secrets on `gardusig/cli`: `TESTPYPI_API_TOKEN` (PR), `PYPI_API_TOKEN` (main), `DOCKERHUB_TOKEN` + `DOCKERHUB_USERNAME` (release).

See [docs/ci-workflows.md](../docs/ci-workflows.md).
