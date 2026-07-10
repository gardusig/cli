# gardusig/cli workflow sync artifacts

Artifacts for keeping the PyPI PR/release pipeline aligned with the workflow library in this repo.

| File | Purpose |
| --- | --- |
| `pull-request-python-cli.yaml` | Fallback PR contract when app `.github/pull-request.yaml` is absent |
| `release-python-cli.yaml` | Release contract (`release` → `pypi-consumer`) |
| `pull-request-router-release-version.patch` | Adds `--release-version` from `app-src/pyproject.toml` to `cli pipeline docker run` |

Confirm GitHub repository secrets on `gardusig/cli`:

| Secret | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload |
| `PYPI_API_TOKEN` | Tag release publish |
| `CENTRAL_PIPELINE_PAT` | Checkout + pipeline dispatch |

First production release: merge to `main`, push tag `vX.Y.Z` matching `pyproject.toml`, verify
[`.github/workflows/release.workflow.yaml`](../.github/workflows/release.workflow.yaml) publishes to PyPI and runs consumer integration.
