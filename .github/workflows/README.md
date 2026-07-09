# CI workflows

Two files — each is a GitHub Actions workflow that only runs `docker build -f .github/Dockerfile --target …`. All commands live in [`.github/Dockerfile`](../Dockerfile) → `scripts/ci/*.sh`.

| File | Trigger | Docker targets |
| --- | --- | --- |
| `pull-request.yaml` | PR to `main` | `pr` → `testpypi-consumer` |
| `release.yaml` | Tag `v*` | `release` → `pypi-consumer` |

PR stage `pr` chains `version-check.sh`, `unit-test.sh`, and `pypi-test.sh` in one image build.

Secrets on `gardusig/cli`: `TESTPYPI_API_TOKEN` (PR), `PYPI_API_TOKEN` (release), `DOCKERHUB_TOKEN` + `DOCKERHUB_USERNAME` (registry push).
