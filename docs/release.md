# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync).

PR CI compares the PR version against `main` via `scripts/ci/version-check.sh`. The workflow resolves `BASE_VERSION` on the runner (`scripts/ci/host-base-version.sh`) and passes it as a Docker build-arg — **no git inside the image**. The PR version must be **strictly greater** than `main`.

Example: `main` ships `1.0.3`; a release candidate PR bumps to **`1.1.0`** (or the next semver).

## PR pipeline (four sequential jobs)

Linear publish path on every PR (selective package legs run in parallel on the hub but cannot replace unit coverage):

| Job | Docker target(s) | Script |
| --- | --- | --- |
| 1 — Version | `version-check` | `scripts/ci/version-check.sh` |
| 2 — Unit tests | `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| 3 — TestPyPI | `pypi-test` | `scripts/ci/pypi-test.sh` → TestPyPI |
| 4 — Post-publish | `integration-test`, then `testpypi-consumer` | `scripts/ci/integration-test.sh` then `scripts/ci/testpypi-consumer.sh` → `scripts/ci/consumer/run.sh` |

Unit and integration stages enforce hard limits of **5 minutes** and **10 minutes** respectively (`CI_UNIT_TIMEOUT`, `CI_INTEGRATION_TIMEOUT`; see [ci-workflows.md](ci-workflows.md)).

Config: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml). Hub mirror: [`docs/yaml-sync/pull-request-python-cli.yaml`](yaml-sync/pull-request-python-cli.yaml).

## Release pipeline (tag `v*` or manual)

On tag push matching `v*` or `workflow_dispatch`:

1. Build sdist/wheel on the runner
2. Publish to PyPI via trusted publishing (`pypa/gh-action-pypi-publish`), with optional `PYPI_API_TOKEN` twine fallback
3. `pypi-consumer` Docker target installs `gardusig-cli==$CLI_RELEASE_VERSION` from PyPI and runs consumer integration

Config: [`.github/workflows/release.yaml`](../.github/workflows/release.yaml).

Tag `vX.Y.Z` must match `pyproject.toml` (see `config/tag.yaml`).

## Scripts ⊥ CLI boundary

CI shell under `scripts/ci/` and `scripts/test/` must not invoke `cli …` or `python3 -m src`. Exception: `scripts/ci/consumer/` runs the **pip-installed** `cli` binary after TestPyPI/PyPI install.

Local maintainer flows may still use `cli`:

```bash
export TESTPYPI_API_TOKEN='pypi-...'
bash scripts/ci/unit-test.sh
bash scripts/ci/pypi-test.sh
```

## GitHub secrets and trusted publishing

Configure on **`gardusig/cli`**:

| Secret / setting | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload (`pypi-test` job) |
| `PYPI_API_TOKEN` | Optional twine fallback when OIDC is unavailable |
| **Trusted publisher** (preferred) | PyPI → Publishing → Add → GitHub Actions |

Trusted publisher claims for this repo (from `release.yaml` on `main`):

| Claim | Value |
| --- | --- |
| Owner | `gardusig` |
| Repository | `cli` |
| Workflow name | `release.yaml` |
| Environment | *(leave empty unless using `release` environment)* |

Manual re-publish:

```bash
gh workflow run release.yaml -R gardusig/cli --ref main
```

## Install contract

Package name **`gardusig-cli`**, console script **`cli`**:

```bash
pip install gardusig-cli
cli --version
```

## Pre-merge checklist (release candidate PR)

```bash
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build -f .github/Dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
bash scripts/ci/unit-test.sh
uv run pytest tests/meta/ tests/services/test_pipeline_selective.py \
  tests/services/test_pipeline_runtime.py -q
```

Confirm PR CI is green on GitHub Actions (see [ci-workflows.md](ci-workflows.md)).

## Post-merge release (maintainer)

After merge to `main`:

```bash
git checkout main && git pull
# Ensure pyproject.toml version matches the tag you will push
git tag v1.1.1
git push origin v1.1.1
```

GitHub Actions runs [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) → `docker build -f .github/Dockerfile --target release` → `pypi-consumer`.

Alternatively, local publish (maintainer only):

```bash
export PYPI_API_TOKEN='pypi-...'
bash scripts/ci/pypi-release.sh
pip install --upgrade gardusig-cli
cli --version
```

Hub sync for `gardusig/yaml`: see [`docs/yaml-sync/README.md`](yaml-sync/README.md).
