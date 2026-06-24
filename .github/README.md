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

Without `TESTPYPI_API_TOKEN`, the pypi job still builds and verifies `dist/*1.0.0*` artifacts. With the token, upload goes to TestPyPI and the job confirms `gardusig-cli==1.0.0` appears on the [TestPyPI project page](https://test.pypi.org/project/gardusig-cli/) (JSON API).

## release.yml

Runs on **tag push** `v*` (e.g. `v1.0.0` → publish version `1.0.0`). Full instructions: [`docs/release.md`](../docs/release.md).

| Job | What |
| --- | --- |
| `Publish to PyPI` | `./scripts/release.sh` — Docker `cli:release` image, build + upload |

### Secrets (release workflow)

| Secret | Purpose |
| --- | --- |
| `PYPI_API_TOKEN` | Production PyPI upload |

Local release (same as CI):

```bash
export PYPI_API_TOKEN=...
./scripts/release.sh
```
