# gardusig/yaml sync artifacts

These files mirror updates required on [`gardusig/yaml`](https://github.com/gardusig/yaml) for the
PyPI PR/release pipeline. Copy or merge into the yaml repo when hub access is available.

| File | Purpose |
| --- | --- |
| `pull-request-python-cli.yaml` | Fallback PR contract when app `.github/pull-request.yaml` is absent |
| `release-python-cli.yaml` | Release contract (`release` → `pypi-consumer`) |
| `pull-request-router-release-version.patch` | Adds `--release-version` from `app-src/pyproject.toml` to `cli pipeline docker run` |

After merging yaml changes, confirm GitHub repository secrets on `gardusig/cli`:

| Secret | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload |
| `PYPI_API_TOKEN` | Tag release publish |
| `CENTRAL_PIPELINE_PAT` | Checkout + pipeline dispatch |

First production release: merge to `main`, push tag `vX.Y.Z` matching `pyproject.toml`, verify
[`.github/workflows/release.workflow.yaml`](../.github/workflows/release.workflow.yaml) publishes to PyPI and runs consumer integration.
