# GitHub Actions

## test.yml

Runs on **pull requests** only (no branch pushes).

| Status check name | Job | Gate |
| --- | --- | --- |
| `Unit tests (Docker)` | `unit` | `./scripts/test-unit.sh` (≥80% coverage) |
| `Integration tests (Docker)` | `integration` | `./scripts/test-integration.sh` |
| `PyPI packaging (Docker)` | `pypi-test` | `./scripts/test-pypi.sh` (build `1.0.0`, optional TestPyPI) |

Require all checks on `main` in GitHub branch protection settings.

### Secrets (test workflow)

| Secret | Purpose |
| --- | --- |
| `TESTPYPI_API_TOKEN` | Optional — upload `gardusig-cli==1.0.0` to TestPyPI on PRs |

Without `TESTPYPI_API_TOKEN`, the pypi job still builds and verifies `dist/*1.0.0*` artifacts.

## release.yml

Runs on **tag push** `v*` only (e.g. `v1.0.0` → publish version `1.0.0`).

| Job | What |
| --- | --- |
| `Publish to PyPI` | `./scripts/pypi/release.sh` — sets version from tag, build + upload |

### Secrets (release workflow)

| Secret | Purpose |
| --- | --- |
| `PYPI_API_TOKEN` | Production PyPI upload |

Local tag release (same as CI):

```bash
git tag v1.0.0
git push origin v1.0.0
# or locally:
export PYPI_API_TOKEN=...
./scripts/pypi/release.sh
```
