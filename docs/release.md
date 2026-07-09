# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync).

PR CI compares the PR version against `main` via `scripts/ci/version-check.sh`. The workflow resolves `BASE_VERSION` on the runner (`scripts/ci/host-base-version.sh`) and passes it as a Docker build-arg — **no git inside the image**. The PR version must be **strictly greater** than `main`.

Example: `main` ships `1.0.3`; a release candidate PR bumps to **`1.1.0`** (or the next semver).

## PR pipeline (four sequential jobs)

| Job | Docker target | Script |
| --- | --- | --- |
| 1 — Validate version | `version-check` | `scripts/ci/version-check.sh` |
| 2 — Unit tests | `unit-test` | `scripts/ci/unit-test.sh` (≥80% via `coverage-unit.ini`) |
| 3 — Publish to TestPyPI | `pypi-test` | `scripts/ci/pypi-test.sh` |
| 4 — TestPyPI install + integration | `testpypi-verify` | `scripts/ci/testpypi-verify.sh` (pip install → consumer → integration) |

Unit and integration stages enforce hard limits of **5 minutes** and **10 minutes** respectively (`CI_UNIT_TIMEOUT`, `CI_INTEGRATION_TIMEOUT`; see [ci-workflows.md](ci-workflows.md)).

Config: [`.github/workflows/pull-request.yaml`](../.github/workflows/pull-request.yaml).

## Main pipeline (merge to `main`)

On every push to `main`:

| Job | Docker target | Script |
| --- | --- | --- |
| Publish to PyPI | `release` | `scripts/ci/pypi-release.sh` |
| PyPI consumer | `pypi-consumer` | `scripts/ci/pypi-consumer.sh` |

Config: [`.github/workflows/main.yaml`](../.github/workflows/main.yaml).

## Release pipeline (tag `v*` only)

On tag push matching `v*`:

1. Build `.github/images/cli-runtime.Dockerfile` — `pip install gardusig-cli==$VERSION` from PyPI (no repo source)
2. Push `binarylifter/gardusig-cli:$VERSION` and `:latest` to Docker Hub
3. `docker pull` + `cli --version` smoke test
4. Create GitHub release for the tag

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
| `PYPI_API_TOKEN` | Main PyPI publish (`main.yaml` → `release` target) |
| `DOCKERHUB_TOKEN` | Release Docker image push |
| `DOCKERHUB_USERNAME` | Release Docker image push (`binaryLifter`) |

Re-publish to PyPI after merge:

```bash
gh workflow run main.yaml -R gardusig/cli --ref main
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
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build -f .github/Dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
bash scripts/ci/unit-test.sh
uv run pytest tests/meta/ tests/services/test_pipeline_selective.py \
  tests/services/test_pipeline_runtime.py -q
```

Confirm PR CI is green on GitHub Actions (see [ci-workflows.md](ci-workflows.md)).

## Post-merge release (maintainer)

After merge to `main`, GitHub Actions runs [`.github/workflows/main.yaml`](../.github/workflows/main.yaml) → PyPI publish → `pypi-consumer`.

Then tag for the Docker image and GitHub release:

```bash
git checkout main && git pull
# Ensure pyproject.toml version matches the tag you will push
git tag v1.1.1
git push origin v1.1.1
```

Tag push runs [`.github/workflows/release.yaml`](../.github/workflows/release.yaml) → Docker Hub image → GitHub release.

Alternatively, local publish (maintainer only):

```bash
export PYPI_API_TOKEN='pypi-...'
bash scripts/ci/pypi-release.sh
pip install --upgrade gardusig-cli
cli --version
```

Hub sync for `gardusig/cli`: see [`docs/yaml-sync/README.md`](yaml-sync/README.md).
