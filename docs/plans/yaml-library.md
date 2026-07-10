# Workflow library (`gardusig/cli`)

## Model

| Layer | Location | Owns |
| --- | --- | --- |
| **Library** | `gardusig/cli` (`.github/workflows/`, `config/ci/catalog.yaml`, `docker/hub/`) | Reusable `workflow_call` routers, PR gate configs, hub images |
| **App repo** | Language repos, `chrome-extensions`, … | `Dockerfile`, `.github/workflows/pull-request.yml`, thin job graphs |
| **CLI package** | `gardusig/cli` (`src/`, `scripts/ci/`) | Validation logic, hub dispatch, pipeline scripts |

## Triggers

1. **PR checks** — app `.github/workflows/pull-request.yml` → `workflow_call` → `gardusig/cli/.github/workflows/lib/pull-request-router.yml`
2. **Manual** — `gh workflow run dispatch.yml -R gardusig/cli -f workflow=…`
3. **CLI** — `cli pipeline run pull-request …` → `repository_dispatch` on `gardusig/cli`

## Catalog

See [`config/ci/catalog.yaml`](../../config/ci/catalog.yaml) for registered workflow ids, lib paths, and dispatch types.

## History

Former standalone repos: `gardusig/pipelines` → `gardusig/yaml` → absorbed into `gardusig/cli`.
