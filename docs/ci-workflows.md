# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and one `.github/Dockerfile`. Workflows only run `docker build -f .github/Dockerfile --target …`; all commands live in `scripts/ci/*.sh`.

## Triggers

| Event | Workflow | Docker targets |
| --- | --- | --- |
| Pull request | [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) | `version-check` → `unit-test` → `pypi-test` → `integration-test` + `testpypi-consumer` |
| Tag `v*` | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | `release` → `pypi-consumer` |

## Docker stages

| Target | Script / chain |
| --- | --- |
| `version-check` | `scripts/ci/version-check.sh` |
| `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| `pypi-test` | `scripts/ci/pypi-test.sh` |
| `integration-test` | `scripts/ci/integration-test.sh` |
| `testpypi-consumer` | `scripts/ci/testpypi-consumer.sh` |
| `pr` | `scripts/ci/pr.sh` → version-check + unit-test + pypi-test (local shortcut) |
| `release` | `scripts/ci/pypi-release.sh` |
| `pypi-consumer` | `scripts/ci/pypi-consumer.sh` |

Other targets (`lint`, `repo-hygiene`, `core-gates`, package matrix legs) remain for local/hub use:

```bash
docker build -f .github/Dockerfile --target lint .
docker build -f .github/Dockerfile --target unit-test .
```

## Scripts ⊥ CLI

`scripts/ci/` uses raw `pytest`, `pip`, `twine`, and `git` — not `cli …` or `python3 -m src`. Consumer stages install `gardusig-cli` from TestPyPI/PyPI and run `scripts/ci/consumer/run.sh`.

Hard timeouts (also enforced in `.github/workflows/pull-request.yaml`):

| Stage | Limit | Env override |
| --- | --- | --- |
| Unit tests | 5 minutes | `CI_UNIT_TIMEOUT` |
| Integration tests | 10 minutes | `CI_INTEGRATION_TIMEOUT` |

## Secrets

| Secret | Used by |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR `pypi-test` + `testpypi-consumer` targets |
| `PYPI_API_TOKEN` | Release `release` target |

## Local validation

```bash
uv run pytest tests/meta/test_scripts_cli_independence.py -q
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build -f .github/Dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f .github/Dockerfile --target unit-test .
```

See [release.md](release.md) and [development.md](development.md).
