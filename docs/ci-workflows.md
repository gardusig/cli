# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and two Dockerfiles under `docker/`:

- `docker/pull-request.dockerfile` — PR pipeline (build from source)
- `docker/release.dockerfile` — PyPI publish + lean runtime image
- `docker/.dockerignore` — canonical ignore rules (copied to repo root before `docker build`)

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
cp docker/.dockerignore .dockerignore
docker build -f docker/pull-request.dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f docker/pull-request.dockerfile --target unit-test .
```

See [release.md](release.md) and [development.md](development.md).
