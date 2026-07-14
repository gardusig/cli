# Development

Work in a **standalone clone** of [`gardusig/cli`](https://github.com/gardusig/cli). The profile repo [`gardusig/gardusig`](https://github.com/gardusig/gardusig) mounts this tree as `public/cli/` for browsing only — commit and push from the cli repo itself.

## Setup

```bash
git clone git@github.com:gardusig/cli.git
cd cli
uv sync          # installs runtime + [dependency-groups].dev (see pyproject.toml)
# or: pip install -e ".[dev]"
```

Override config with `CLI_CONFIG_DIR` (default after PyPI install: `~/.config/cli/`). For tests and CI, set `CLI_PROFILE=test` to merge `config.test.yaml` from `tests/fixtures/config/`.

## Tests

```bash
.venv/bin/python -m pytest tests/meta/ -q
.venv/bin/python -m pytest tests/services/test_pipeline_selective.py -q
```

Unit coverage gate (≥80%): `coverage-unit.ini` — enforced in CI via `scripts/pull-request/unit-test.sh`.

## Local Docker CI

All stages delegate to `scripts/pull-request/` and `scripts/release/` (raw shell — no `cli` or `python3 -m src` in those scripts).

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"

docker build -f docker/pull-request.dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f docker/pull-request.dockerfile --target unit-test .
```

Build context stays the repo root; ignore rules live in `docker/.dockerignore` (used via `docker build --ignorefile` when supported, otherwise symlinked to `.dockerignore`).

Git runs **only on the host** (`host-base-version.sh` or the workflow). Docker stages read copied files and build-args.

Pipeline job graphs: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml), [`.github/workflows/release.yaml`](../.github/workflows/release.yaml).

GitHub Actions entrypoints: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml) and [`.github/workflows/release.yaml`](../.github/workflows/release.yaml).

## Boundaries

| Layer | Location | Notes |
| --- | --- | --- |
| CI shell | `scripts/pull-request/`, `scripts/release/` | `pytest`, `pip`, `twine`, `git` |
| Product | `src/` | installable `gardusig-cli` package |
| Consumer smoke | `scripts/pull-request/consumer/` | pip-installed `cli` binary only |

## Release (maintainer)

1. Bump `pyproject.toml` / `src/__init__.py` (strictly greater than `main` for PR gate).
2. Merge PR; push tag `X.Y.Z` matching the version (bare semver, e.g. `1.0.8`).
3. [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) publishes to PyPI and runs consumer integration.

See [release.md](release.md) for secrets and hub sync (`docs/yaml-sync/`).
