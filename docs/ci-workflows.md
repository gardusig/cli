# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and a single root `Dockerfile`:

- `Dockerfile` — PR pipeline (build from source) and release (PyPI + runtime image)
- `.dockerignore` — build context ignore rules

Workflows call `scripts/pull-request/` and `scripts/release/`; Docker stages call matching scripts under those directories.

## Triggers

| Event | Workflow | Pipeline |
| --- | --- | --- |
| Pull request → `main` | [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) | Version gate → unit tests → TestPyPI → consumer integration |
| Push `main` | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | Publish PyPI → lean Docker image |
| Tag `v*` | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | GitHub release |

## Pull request

| Step | Docker target | Script |
| --- | --- | --- |
| Version gate | `version-check` | `scripts/pull-request/version-check.sh` |
| Unit tests | `unit-test` | `scripts/pull-request/unit-test.sh` |
| TestPyPI publish | `testpypi` | `scripts/pull-request/testpypi-release.sh` |
| TestPyPI consumer | `testpypi-consumer` | `scripts/pull-request/testpypi-consumer.sh` |

`BASE_VERSION` is resolved on the runner via `scripts/pull-request/host-last-published-version.sh` (latest PyPI release; empty on first publish).

## Timeouts

Workflow steps and pipeline scripts fail if they exceed their time limit (`timeout` / `timeout-minutes`).

| Variable | Default | Used by |
| --- | --- | --- |
| `CI_UNIT_TIMEOUT` | `5m` | Unit tests (`unit-test.sh`) |
| `CI_INTEGRATION_TIMEOUT` | `3m` | Integration smoke (`integration-smoke.sh`) |
| `CI_DOCKER_BUILD_TIMEOUT` | `10m` | `docker build` wrapper (`build.sh`) |
| `CI_VERSION_CHECK_TIMEOUT` | `2m` | Version gate |
| `CI_TESTPYPI_TIMEOUT` | `8m` | TestPyPI / PyPI publish |
| `CI_CONSUMER_TIMEOUT` | `5m` | Post-install consumer smoke |
| `CI_RESOLVE_TIMEOUT` | `2m` | Version resolve scripts |
| `CI_RELEASE_SMOKE_TIMEOUT` | `3m` | Runtime image smoke |
| `CI_DOCKER_PUSH_TIMEOUT` | `5m` | Docker Hub push |

GitHub Actions also sets per-step `timeout-minutes` on each workflow step (typically 3–12 minutes).

## Release (main merge)

| Job | Docker target | Script |
| --- | --- | --- |
| Publish to PyPI | `pypi` | `scripts/release/pypi-release.sh` |
| Lean runtime image | `runtime` | `pip install gardusig-cli==$VERSION` (no repo source) |

## Secrets

| Secret | Used by |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR `testpypi` target |
| `PYPI_API_TOKEN` | Release `pypi` target |
| `DOCKERHUB_TOKEN` | Release runtime image push |
| `DOCKERHUB_USERNAME` | Release runtime image push |

## Local validation

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"
docker build --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build --target unit-test .
```

See [release.md](release.md) and [development.md](development.md).
