# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync). PR CI requires the PR version to be **greater** than `origin/main` (Docker `version` target + `scripts/ci/version-check.sh`).

Example: `main` ships `1.0.0`; a release candidate PR bumps to **`1.0.1`**.

## Pull request pipeline (main only)

1. **`./scripts/test/pr-step1-build-testpypi.sh`** ? version gate, unit tests, `./scripts/pypi/publish-testpypi.sh` (needs `TESTPYPI_API_TOKEN`).
2. **`./scripts/test/pr-step2-testpypi-usability.sh`** ? `./scripts/pypi/install-testpypi.sh` then `./scripts/test/testpypi/run-all.sh`.

Local equivalents:

```bash
export TESTPYPI_API_TOKEN='pypi-...'
./scripts/test/pr-step1-build-testpypi.sh
./scripts/test/pr-step2-testpypi-usability.sh
```

## Production deploy (official PyPI)

**Not TestPyPI.** Uses `PYPI_API_TOKEN` and `./scripts/pypi/deploy.sh` (wraps `./scripts/pypi/release.sh`).

```bash
export PYPI_API_TOKEN='pypi-...'
./scripts/pypi/deploy.sh
```

Tag push `vX.Y.Z` should match `pyproject.toml` (see `.cli/tag.yaml`).

## Scripts

| Script | Index |
| --- | --- |
| `scripts/pypi/publish-testpypi.sh` | TestPyPI |
| `scripts/pypi/install-testpypi.sh` | TestPyPI (pip) |
| `scripts/pypi/deploy.sh` / `release.sh` | Production PyPI |
| `scripts/pypi/test.sh` | Wrapper ? `publish-testpypi.sh` |
