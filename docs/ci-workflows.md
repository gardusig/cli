# Gardusig CI/CD — Docker pipeline

This repo owns three GitHub Actions workflows and two Dockerfiles:

- `.github/Dockerfile` — PR/main CI stages (build from source)
- `.github/images/cli-runtime.Dockerfile` — release runtime image (install from PyPI only)

Workflows run `docker build -f … --target …`; commands live in `scripts/ci/*.sh`.

## Triggers

| Event | Workflow | Pipeline |
| --- | --- | --- |
| Pull request → `main` | [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) | 1 version → 2 unit → 3 TestPyPI → 4 verify |
| Push `main` | [`.github/workflows/main.yaml`](../.github/workflows/main.yaml) | Publish PyPI → `pypi-consumer` |
| Tag `v*` | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | Runtime image → Docker Hub → pull smoke → GitHub release |

## Pull request (four jobs)

| Job | Docker target | Script chain |
| --- | --- | --- |
| 1 — Validate version | `version-check` | `scripts/ci/version-check.sh` |
| 2 — Unit tests | `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| 3 — Publish to TestPyPI | `pypi-test` | `scripts/ci/pypi-test.sh` |
| 4 — TestPyPI install + integration | `testpypi-verify` | `scripts/ci/testpypi-verify.sh` → consumer + integration |

Job 4 installs `gardusig-cli` from TestPyPI (no editable source install), runs `scripts/ci/consumer/run.sh`, then the integration suite via `scripts/ci/testpypi-integration.sh`.

## Main (merge to main)

| Job | Docker target | Script |
| --- | --- | --- |
| Publish to PyPI | `release` | `scripts/ci/pypi-release.sh` |
| PyPI consumer | `pypi-consumer` | `scripts/ci/pypi-consumer.sh` |

## Release (tag only)

Tag `vX.Y.Z` must match `pyproject.toml`. The release workflow:

1. Builds `.github/images/cli-runtime.Dockerfile` with `pip install gardusig-cli==X.Y.Z` from PyPI (no repo source in the image)
2. Pushes `binarylifter/gardusig-cli:X.Y.Z` and `:latest` to Docker Hub
3. `docker pull` + `cli --version` smoke test
4. Creates a GitHub release for the tag

## Docker stages (CI Dockerfile)

| Target | Script / chain |
| --- | --- |
| `version-check` | `scripts/ci/version-check.sh` |
| `unit-test` | `scripts/ci/unit-test.sh` |
| `pypi-test` | `scripts/ci/pypi-test.sh` |
| `testpypi-verify` | `scripts/ci/testpypi-verify.sh` |
| `testpypi-consumer` | `scripts/ci/testpypi-consumer.sh` (legacy/local) |
| `integration-test` | `scripts/ci/integration-test.sh` (source tree; local/hub) |
| `pr` | `scripts/ci/pr.sh` |
| `release` | `scripts/ci/pypi-release.sh` |
| `pypi-consumer` | `scripts/ci/pypi-consumer.sh` |

## Scripts ⊥ CLI

`scripts/ci/` uses raw `pytest`, `pip`, `twine`, and `git` — not `cli …` or `python3 -m src`. Consumer and verify stages install `gardusig-cli` from TestPyPI/PyPI and run the pip-installed `cli` binary.

Hard timeouts (also enforced in workflows):

| Stage | Limit | Env override |
| --- | --- | --- |
| Unit tests | 5 minutes | `CI_UNIT_TIMEOUT` |
| Integration tests | 10 minutes | `CI_INTEGRATION_TIMEOUT` |

## Secrets

| Secret | Used by |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR `pypi-test` + `testpypi-verify` |
| `PYPI_API_TOKEN` | Main `release` target |
| `DOCKERHUB_TOKEN` | Release image push |
| `DOCKERHUB_USERNAME` | Release image push |

## Local validation

```bash
uv run pytest tests/meta/test_scripts_cli_independence.py -q
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build -f .github/Dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f .github/Dockerfile --target unit-test .
```

See [release.md](release.md) and [development.md](development.md).
