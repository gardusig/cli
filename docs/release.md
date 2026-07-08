# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync).

PR CI compares the PR version against `main` via `scripts/ci/version-check.sh`. The workflow resolves `BASE_VERSION` on the runner (`scripts/ci/host-base-version.sh`) and passes it as a Docker build-arg — **no git inside the image**. The PR version must be **strictly greater** than `main`.

Example: `main` ships `1.0.2`; a release candidate PR bumps to **`1.0.3`**.

## PR pipeline (four sequential jobs)

Linear publish path on every PR (selective package legs run in parallel on the hub but cannot replace unit coverage):

| Job | Docker target(s) | Script |
| --- | --- | --- |
| 1 — Version | `version-check` | `scripts/ci/version-check.sh` |
| 2 — Unit tests | `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| 3 — TestPyPI | `pypi-test` | `scripts/ci/pypi-test.sh` → TestPyPI |
| 4 — Post-publish | `integration-test`, then `testpypi-consumer` | `scripts/ci/integration-test.sh` then `scripts/ci/testpypi-consumer.sh` → `scripts/ci/consumer/run.sh` |

Unit and integration stages enforce hard limits of **5 minutes** and **10 minutes** respectively (`CI_UNIT_TIMEOUT`, `CI_INTEGRATION_TIMEOUT`; see [ci-workflows.md](ci-workflows.md)).

Config: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml). Hub fallback: [`docs/yaml-sync/pull-request-python-cli.yaml`](yaml-sync/pull-request-python-cli.yaml).

`pypi` / `testpypi-consumer` always `needs: unit` (enforced in `src/services/pipeline_selective.py`).

## Release pipeline (tag `v*`)

On tag push matching `v*`:

1. `release` target → `scripts/ci/pypi-release.sh` (production PyPI)
2. `pypi-consumer` target → install `gardusig-cli==$CLI_RELEASE_VERSION` from PyPI and run consumer integration

Config: [`.github/workflows/release.yaml`](../.github/workflows/release.yaml). Workflow caller: [`.github/workflows/release.workflow.yaml`](../.github/workflows/release.workflow.yaml).

Tag `vX.Y.Z` must match `pyproject.toml` (see `config/tag.yaml`).

## Scripts ⊥ CLI boundary

CI shell under `scripts/ci/` and `scripts/test/` must not invoke `cli …` or `python3 -m src`. Exception: `scripts/ci/consumer/` runs the **pip-installed** `cli` binary after TestPyPI/PyPI install.

Local maintainer flows may still use `cli`:

```bash
export TESTPYPI_API_TOKEN='pypi-...'
bash scripts/ci/unit-test.sh
bash scripts/ci/pypi-test.sh
```

## GitHub secrets

Configure on **`gardusig/cli`** (not in repo):

| Secret | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload (`pypi-test` job) |
| `PYPI_API_TOKEN` | Tag release publish (`release` job) |
| `CENTRAL_PIPELINE_PAT` | Pipeline checkout + dispatch |

## Install contract

Package name **`gardusig-cli`**, console script **`cli`**:

```bash
pip install gardusig-cli
cli --version
```

## Pre-merge checklist (release candidate PR)

```bash
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
bash scripts/ci/unit-test.sh
uv run pytest tests/meta/ tests/services/test_pipeline_selective.py \
  tests/services/test_pipeline_runtime.py -q
```

Confirm central CI is green (hub: `gardusig/yaml` pull-request router + `python-cli.yaml`).

## Post-merge release (maintainer)

After merge to `main`:

```bash
git checkout main && git pull
# Ensure pyproject.toml version matches the tag you will push
git tag v1.0.3
git push origin v1.0.3
```

GitHub Actions runs [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) → `docker build --target release` → `pypi-consumer`.

Alternatively, local publish (maintainer only):

```bash
export PYPI_API_TOKEN='pypi-...'
bash scripts/ci/pypi-release.sh
pip install --upgrade gardusig-cli
cli --version
```

Hub sync for `gardusig/yaml`: see [`docs/yaml-sync/README.md`](yaml-sync/README.md).
