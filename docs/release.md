# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). Pull request CI uses [TestPyPI](https://test.pypi.org/project/gardusig-cli/) only.

## Version source

Canonical version: `pyproject.toml` and `src/__init__.py` (kept in sync). PR CI requires the PR version to be **greater** than `origin/main` (Docker `version` target + `src/scripts/ci/version-check.sh`).

Example: `main` ships `1.0.0`; a release candidate PR bumps to **`1.0.1`**.

## Pull request pipeline (main only)

1. `cli lint repo /workspace`
2. `cli test python unit /workspace`
3. `cli pypi upload --testpypi` with `TESTPYPI_API_TOKEN`
4. TestPyPI consumer install from a clean image

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

## Commands

| Command | Index |
| --- | --- |
| `cli pypi upload --testpypi` | TestPyPI |
| `cli pypi upload` | Production PyPI |
| `cli release main` | Tag, publish, verify, GitHub release |
