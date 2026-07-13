# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync).

PR CI compares the PR version against the **last published PyPI version** via `scripts/pull-request/version-check.sh`. The workflow resolves `BASE_VERSION` on the runner (`scripts/pull-request/host-last-published-version.sh`) and passes it as a Docker build-arg — **no git inside the image**. When nothing is published yet, the gate is skipped. Otherwise the PR version must be **strictly greater** than the last PyPI release.

To bump and write the next compatible version locally:

```bash
bash scripts/pull-request/set-version.sh          # writes pyproject.toml + src/__init__.py
bash scripts/pull-request/version-suggest.sh      # print only
cli pypi version set                              # same write path via CLI
cli pypi version suggest                          # print only
```

On the first publish (nothing on PyPI yet), `set-version` keeps a valid `pyproject.toml` version or defaults to **`0.1.0`**.

Example: `main` ships `1.0.3`; a release candidate PR bumps to **`1.1.0`** (or the next semver).

## PR pipeline

| Step | Docker target | Script |
| --- | --- | --- |
| Validate version | `version-check` | `scripts/pull-request/version-check.sh` |
| Unit tests | `unit-test` | `scripts/pull-request/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| TestPyPI publish | `testpypi` | `scripts/pull-request/testpypi-release.sh` |
| TestPyPI consumer | `testpypi-consumer` | `scripts/pull-request/testpypi-consumer.sh` |

Config: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml).

## Main pipeline (merge to `main`)

On every push to `main`:

| Job | Docker target | Script |
| --- | --- | --- |
| Publish to PyPI | `pypi` | `scripts/release/pypi-release.sh` |
| Lean Docker image | `runtime` | `pip install gardusig-cli==$VERSION` (no repo source) |

Config: [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) (push `main`).

## Release pipeline (tag `v*` only)

On tag push matching `v*`:

1. Create GitHub release for the tag

Docker image publish runs on `main` after PyPI (not on tag push).

Tag `vX.Y.Z` must match `pyproject.toml` (see `config/tag.yaml`).

## Scripts ⊥ CLI boundary

CI shell under `scripts/pull-request/` and `scripts/release/` must not invoke `cli …` or `python3 -m src`. Exception: `scripts/pull-request/consumer/` runs the **pip-installed** `cli` binary after PyPI install.

Local maintainer flows may still use `cli`:

```bash
export TESTPYPI_API_TOKEN='pypi-...'
bash scripts/pull-request/unit-test.sh
bash scripts/release/pypi-release.sh
```

## GitHub secrets and trusted publishing

Configure on **`gardusig/cli`**:

| Secret / setting | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload (`pypi-test` job) |
| `PYPI_API_TOKEN` | Main PyPI publish (`release.yaml` → `pypi` target) |
| `DOCKERHUB_TOKEN` | Release Docker image push |
| `DOCKERHUB_USERNAME` | Release Docker image push (`binaryLifter`) |

Re-publish to PyPI after merge:

```bash
Push the branch and open a pull request in the hosting UI, or merge via your usual git workflow.
```

Publish Docker image + GitHub release:

```bash
git tag v1.1.1 && git push origin v1.1.1
```

## Install contract

Package name **`gardusig-cli`**, console script **`cli`**:

```bash
pip install gardusig-cli
cli --version
```

## Pre-merge checklist (release candidate PR)

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"
docker build --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
bash scripts/pull-request/unit-test.sh
uv run pytest tests/meta/ tests/services/test_pipeline_selective.py \
  tests/services/test_pipeline_runtime.py -q
```

Confirm PR CI is green on GitHub Actions (see [ci-workflows.md](ci-workflows.md)).

## Post-merge release (maintainer)

After merge to `main`, GitHub Actions runs [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) → PyPI publish → lean Docker image on Docker Hub.

Tag push creates the GitHub release:

```bash
git checkout main && git pull
# Ensure pyproject.toml version matches the tag you will push
git tag v1.1.1
git push origin v1.1.1
```

Tag push runs the `github-release` job in [`.github/workflows/release.yaml`](../.github/workflows/release.yaml).

Alternatively, local publish (maintainer only):

```bash
export PYPI_API_TOKEN='pypi-...'
bash scripts/release/pypi-release.sh
pip install --upgrade gardusig-cli
cli --version
```

Hub sync for `gardusig/cli`: see [`docs/yaml-sync/README.md`](yaml-sync/README.md).
