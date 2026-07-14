# gardusig/cli workflow sync artifacts

Reference contracts for aligning language-repo pipelines with this repo's PR/release Docker stages.

| File | Purpose |
| --- | --- |
| `pull-request-python-cli.yaml` | Fallback PR contract when an app `.github/pull-request.yaml` is absent |
| `release-python-cli.yaml` | Release contract (`pypi` → `runtime`) |
| `pull-request-router-release-version.patch` | Adds `--release-version` from `app-src/pyproject.toml` to `cli pipeline docker run` |

Secrets on **`gardusig/cli`**:

| Secret | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | PR TestPyPI upload |
| `PYPI_API_TOKEN` | Tag release publish |
| `DOCKERHUB_TOKEN` / `DOCKERHUB_USERNAME` | Release runtime image push |

First production release: merge to `main`, push tag `X.Y.Z` matching `pyproject.toml`, verify
[`.github/workflows/release.yaml`](../.github/workflows/release.yaml) publishes to PyPI and pushes the Docker image.
