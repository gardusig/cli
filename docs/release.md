# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync). PR CI requires the PR version to be **greater** than `origin/main` via `cli pypi version check`.

Example: `main` ships `1.0.1`; a release candidate PR bumps to **`1.0.2`** (strictly greater than base).

## Repository boundary

`python-cli` owns package metadata, release commands, version checks, and tests. `gardusig/github-pipelines` owns workflow YAML, Dockerfiles, schedules, branch protection, trusted publishing/OIDC setup, and repository secrets.

Do not add `.github/workflows/`, Dockerfiles, or publish shell scripts to this repo for PyPI releases.

## Pull request pipeline

The central pipeline should call repo-local command contracts:

1. `cli pypi version check --base origin/main`
2. `cli test packages resolve --base "$BASE_SHA" --head "$HEAD_SHA" --format json`
3. Package unit/integration commands from `cli test packages run PACKAGE`
4. `cli pypi upload --testpypi --skip-existing` with `TESTPYPI_API_TOKEN`
5. TestPyPI consumer install from a clean image

Local equivalents:

```bash
export TESTPYPI_API_TOKEN='pypi-...'
cli test python unit .
cli pypi upload --yes --testpypi --skip-existing
```

## Production deploy (official PyPI)

**Not TestPyPI.** Uses `PYPI_API_TOKEN` and the guarded release command.

```bash
export PYPI_API_TOKEN='pypi-...'
cli release main --yes
```

Tag push `vX.Y.Z` should match `pyproject.toml` (see `config/tag.yaml`).

For lower-level publishing, maintainers can use `cli pypi upload --yes`, but `cli release main --yes` is the preferred production path because it creates/pushes the tag, publishes, verifies the PyPI project page, and creates the GitHub release.

## Commands

| Command | Index |
| --- | --- |
| `cli pypi upload --testpypi` | TestPyPI |
| `cli pypi upload` | Production PyPI |
| `cli release main` | Tag, publish, verify, GitHub release |

## Install contract

The package name is **`gardusig-cli`** and the installed console command is **`cli`**:

```bash
pip install gardusig-cli
cli --version
```

## Pre-merge checklist (release candidate PR)

Run on the PR branch before merge:

```bash
uv run python -m src pypi version check --base origin/main
uv run python tests/integration/check_integration_coverage.py
uv run pytest tests/meta/ tests/services/test_pipeline_selective.py \
  tests/services/test_pipeline_runtime.py -q
uv run pytest tests/git/ tests/gh/ tests/docker/ tests/chrome/ \
  tests/notion/ tests/drive/ tests/contest/ tests/project/ tests/pypi/ -q
```

Confirm central CI is green after [github-pipelines PR #20](https://github.com/gardusig/github-pipelines/pull/20) merges (needs `--force-full-suite` from PR #88). Until PyPI ships **1.0.2**, workflows install `gardusig-cli` from editable `app-src` or git `main`.

**Merge order:** python-cli PR #88 → pipelines PR #20 → `cli release main --yes`.

## Post-merge release (maintainer)

After the release candidate PR merges to `main`:

```bash
git checkout main && git pull
export PYPI_API_TOKEN='pypi-...'
cli release main --yes
pip install --upgrade gardusig-cli
cli --version
```

Then bump `main` to the next patch (e.g. `1.0.3`) for the next PR version gate, and close issues documented in `docs/public-cli-hardening.md`.
