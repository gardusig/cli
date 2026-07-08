# Gardusig CI/CD — Docker pipeline

This repo owns two GitHub Actions workflows and one root `Dockerfile`. Workflows only run `docker build --target …`; all commands live in `scripts/ci/*.sh`.

## Triggers

| Event | Workflow | Docker targets |
| --- | --- | --- |
| Pull request | [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) | `pr` → `testpypi-consumer` |
| Tag `v*` | [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) | `release` → `pypi-consumer` |

## Docker stages

| Target | Script / chain |
| --- | --- |
| `pr` | `scripts/ci/pr.sh` → version-check + unit-test + pypi-test |
| `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| `pypi-test` | `scripts/ci/pypi-test.sh` |
| `testpypi-consumer` | `scripts/ci/testpypi-consumer.sh` |
| `release` | `scripts/ci/pypi-release.sh` |
| `pypi-consumer` | `scripts/ci/pypi-consumer.sh` |

Other targets (`lint`, `repo-hygiene`, `core-gates`, package matrix legs) remain for local/hub use:

```bash
docker build --target lint .
docker build --target unit-test .
```

## Scripts ⊥ CLI

`scripts/ci/` uses raw `pytest`, `pip`, `twine`, and `git` — not `cli …` or `python3 -m src`. Consumer stages install `gardusig-cli` from TestPyPI/PyPI and run `scripts/ci/consumer/run.sh`.

## Secrets

| Secret | Used by |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR `pr` target (`pypi-test.sh`) |
| `PYPI_API_TOKEN` | Release `release` target |

## Local validation

```bash
uv run pytest tests/meta/test_scripts_cli_independence.py -q
docker build --target pr --build-arg CLI_RELEASE_VERSION=1.0.3 .
```

See [release.md](release.md) and [development.md](development.md).
