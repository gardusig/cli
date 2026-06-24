# GitHub Actions

## test.yml

Runs on **pull requests** only (no branch pushes).

| Status check name | Job | Gate |
| --- | --- | --- |
| `Unit tests (Docker)` | `unit` | `./scripts/test-unit.sh` (≥80% coverage) |
| `Integration tests (Docker)` | `integration` | `./scripts/test-integration.sh` |

Require both status checks on `main` in GitHub branch protection settings.

## release.yml

Runs on **tag push** `v*` (e.g. `v0.1.0`) and optional **workflow_dispatch**.

| Job | What |
| --- | --- |
| `Publish to PyPI` | `python -m build` + twine upload `gardusig-cli` |

Configure repo secret **`PYPI_API_TOKEN`**.

Local tag release (same as CI):

```bash
./scripts/release-pypi.sh
# or: ./scripts/release.sh
```
