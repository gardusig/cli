# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and two Dockerfiles under `docker/`:

- `docker/pull-request.dockerfile` — PR pipeline (per-target `COPY` lists)
- `docker/release.dockerfile` — release (PyPI publish + runtime image)

Workflows call `scripts/pull-request/` and `scripts/release/`; Docker stages call matching scripts under those directories.

## Triggers

| Event | Workflow | Pipeline |
| --- | --- | --- |
| Pull request → `main` | [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) | Version check → unit tests → TestPyPI publish → TestPyPI consumer |
| Tag push | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | PyPI → Docker image → GitHub release |

## Version formats

| Target | Format | Example |
| --- | --- | --- |
| Git tag | `X.Y.Z` | `1.0.7` |
| PyPI | `X.Y.Z` | `1.0.7` |
| Docker Hub | `X.Y.Z` + `latest` | `binarylifter/gardusig-cli:1.0.7` |

Push git tag `1.0.7` to run the full release pipeline. Tags must match semver `X.Y.Z` (a leading `v` is accepted and stripped for PyPI/Docker).

## Pull request

| Step | Docker target | Script |
| --- | --- | --- |
| Version gate | `version-check` | `scripts/pull-request/version-check.sh` |
| Unit tests | `unit-test` | `scripts/pull-request/unit-test.sh` |
| TestPyPI publish | `testpypi` | `scripts/pull-request/testpypi-release.sh` |
| TestPyPI consumer | `testpypi-consumer` | `scripts/pull-request/testpypi-consumer.sh` |

`BASE_VERSION` is resolved on the runner via `scripts/pull-request/host-last-published-version.sh` (greatest semver on PyPI or TestPyPI; empty on first publish).

## Timeouts

Workflow steps and pipeline scripts fail if they exceed their time limit (`timeout` / `timeout-minutes`).

| Variable | Default | Used by |
| --- | --- | --- |
| `CI_UNIT_TIMEOUT` | `5m` | Unit tests (`unit-test.sh`) |
| `CI_INTEGRATION_TIMEOUT` | `3m` | Integration smoke (`integration-smoke.sh`) |
| `CI_DOCKER_BUILD_TIMEOUT` | `5m` | `docker build` wrapper (`build.sh`) |
| `CI_VERSION_CHECK_TIMEOUT` | `2m` | Version gate |
| `CI_TESTPYPI_TIMEOUT` | `5m` | TestPyPI / PyPI publish |
| `CI_CONSUMER_TIMEOUT` | `5m` | Post-install consumer smoke |
| `CI_RESOLVE_TIMEOUT` | `2m` | Version resolve scripts |
| `CI_RELEASE_SMOKE_TIMEOUT` | `3m` | Runtime image smoke |
| `CI_DOCKER_PUSH_TIMEOUT` | `5m` | Docker Hub push |

GitHub Actions also sets per-step `timeout-minutes` on each workflow step (typically 3–12 minutes).

## Release (tag `*`)

Triggered by pushing a git tag; `resolve-tag-version.sh` accepts only semver `X.Y.Z` (legacy `vX.Y.Z` is stripped).

| Job | Purpose |
| --- | --- |
| Resolve version | `1.0.7` → PyPI/Docker `1.0.7` |
| Publish to PyPI | `gardusig-cli==1.0.7` |
| Docker image | `pip install gardusig-cli==1.0.7` → push `:1.0.7` and `:latest` |
| GitHub release | Create release for tag `1.0.7` |

## Secrets

| Secret | Used by |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR `testpypi` target |
| `PYPI_API_TOKEN` | Release `pypi` target |
| `DOCKERHUB_TOKEN` | Release runtime image push |
| `DOCKERHUB_USERNAME` | Release runtime image push |

## Local validation

Compare host scripts vs both Dockerfiles:

```bash
bash scripts/local/compare-docker-pipelines.sh
```

Or run stages individually:

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"
docker build -f docker/pull-request.dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f docker/pull-request.dockerfile --target unit-test .
docker build -f docker/release.dockerfile --target runtime --build-arg "CLI_VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open(\"pyproject.toml\",\"rb\"))[\"project\"][\"version\"])')" .
```

See [release.md](release.md) and [development.md](development.md).
