# Workflow catalog (this repo)

`gardusig/cli` CI is defined in [`.github/workflows/`](../.github/workflows/).

| Workflow | Purpose |
| --- | --- |
| `pull-request.yaml` | PR Docker pipeline: version-check → unit-test → testpypi → consumer |
| `release.yaml` | Tag on `main`: PyPI publish + runtime Docker image |

Dockerfiles: `docker/pull-request.dockerfile`, `docker/release.dockerfile`.

Scripts: `scripts/pull-request/`, `scripts/release/`.

Run locally:

```bash
./scripts/pull-request/build-pr-image.sh
cli test python unit .
```
