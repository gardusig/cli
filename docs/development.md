# Development

Work in a **standalone clone** of [`gardusig/cli`](https://github.com/gardusig/cli). The profile repo [`gardusig/gardusig`](https://github.com/gardusig/gardusig) mounts this tree as `public/cli/` for browsing only — commit and push from the cli repo itself.

## Setup

```bash
git clone git@github.com:gardusig/cli.git
cd cli
uv sync
```

Override config with `CLI_CONFIG_DIR` (default: `config/` in the clone, or `~/.config/cli/` after PyPI install).

## Tests

```bash
.venv/bin/python -m pytest tests/meta/ -q
.venv/bin/python -m pytest tests/services/test_pipeline_selective.py -q
```

Unit coverage gate (≥80%): `coverage-unit.ini` — enforced in CI via `scripts/ci/unit-test.sh`.

## Local Docker CI

All stages delegate to `scripts/ci/*.sh` (raw shell — no `cli` or `python3 -m src` in those scripts).

```bash
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
export CLI_RELEASE_VERSION="$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"

docker build -f .github/Dockerfile --target lint .
docker build -f .github/Dockerfile --target unit-test .
docker build -f .github/Dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f .github/Dockerfile --target pypi-test --build-arg "CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION}" .
```

Git runs **only on the host** (`host-base-version.sh` or the workflow). Docker stages read copied files and build-args.

Pipeline job graphs: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml), [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) (each file is a workflow that only invokes Docker targets).

GitHub Actions entrypoints: same files — see [`.github/workflows/README.md`](../.github/workflows/README.md).

## Boundaries

| Layer | Location | Notes |
| --- | --- | --- |
| CI shell | `scripts/ci/` | `pytest`, `pip`, `twine`, `git` |
| Product | `src/` | installable `gardusig-cli` package |
| Hub routers | `gardusig/cli` | `workflow_call` orchestration |
| Consumer smoke | `scripts/ci/consumer/` | pip-installed `cli` binary only |

## Release (maintainer)

1. Bump `pyproject.toml` / `src/__init__.py` (strictly greater than `main` for PR gate).
2. Merge PR; push tag `vX.Y.Z` matching the version.
3. [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) publishes to PyPI and runs consumer integration.

See [release.md](release.md) for secrets and hub sync (`docs/yaml-sync/`).
