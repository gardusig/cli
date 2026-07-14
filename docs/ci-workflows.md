# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and two Dockerfiles under `docker/`:

- `docker/pull-request.dockerfile` — PR pipeline (per-target `COPY` lists)
- `docker/release.dockerfile` — release (PyPI publish + runtime image)

Workflows only orchestrate `docker build` and `docker run`. All pipeline logic lives in `scripts/` and runs inside Docker stages (or `ci-tools` for host-docker operations like push/smoke/release).

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

| Step | Orchestration | Docker target | Script (inside image) |
| --- | --- | --- | --- |
| Resolve versions | `docker build` + `docker run` | `resolve` | `scripts/pull-request/resolve-version.sh` |
| Version gate | `docker build` | `version-check` | `scripts/pull-request/version-check.sh` |
| Unit tests | `docker build` | `unit-test` | `scripts/pull-request/unit-test.sh` |
| TestPyPI publish | `docker build` | `testpypi` | `scripts/pull-request/testpypi-release.sh` |
| TestPyPI consumer | `docker build` | `testpypi-consumer` | `scripts/pull-request/testpypi-consumer.sh` |

`BASE_VERSION` is resolved inside the `resolve` Docker stage via `scripts/pull-request/host-last-published-version.sh` (greatest semver on PyPI or TestPyPI; empty on first publish).

## Timeouts

GitHub Actions step limits use tier labels from `scripts/workflow/workflow-step-tiers.yaml`:

| Tier | Minutes | Typical steps |
| --- | --- | --- |
| `short` | 3 | checkout, buildx, resolve, login |
| `medium` | 6 | docker build (fast), push, consumer |
| `long` | 9 | unit-test docker build |

Each job `timeout-minutes` is the **sum** of its step timeouts. Apply or verify:

```bash
bash scripts/workflow/sum-job-timeouts.sh      # print sums from config
bash scripts/workflow/apply-timeouts.sh        # write step + job timeouts
bash scripts/workflow/apply-timeouts.sh --check
```

Pipeline scripts enforce limits via `CI_*_TIMEOUT` and `stage_run_with_timeout` (set in Dockerfiles, not workflow YAML).

## Release (tag `*`)

Triggered by pushing a git tag; `resolve-tag-version.sh` runs in the `resolve` Docker stage and accepts only semver `X.Y.Z` (legacy `vX.Y.Z` is stripped).

| Job | Orchestration | Purpose |
| --- | --- | --- |
| Resolve version | `docker build` + `docker run` | `1.0.7` → PyPI/Docker `1.0.7` |
| Publish to PyPI | `docker build` | `gardusig-cli==1.0.7` |
| Docker image | `docker build` + `ci-tools` `docker run` | Build runtime, push `:1.0.7` and `:latest`, smoke |
| GitHub release | `ci-tools` `docker run` | Create release for tag `1.0.7` |

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
