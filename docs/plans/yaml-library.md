# Workflow library (`gardusig/cli`)

## Model

| Layer | Location | Owns |
| --- | --- | --- |
| **Library** | `gardusig/cli` (submodule: `index/devops/yaml/`) | Reusable `workflow_call` routers, `catalog.yaml`, hub images (`docker/operator`, `docker/cli-base`) |
| **App repo** | `gardusig/cli`, language repos, … | `Dockerfile`, `.github/workflows/*.yaml`, thin `*.workflow.yaml` callers |
| **App-specific automation** | Same app repo | `.github/workflows/release.yaml`, `.github/workflows/repo-review.yaml` |

## Triggers

1. **PR checks** — app `.github/workflows/pull-request.workflow.yaml` → `workflow_call` → `gardusig/cli/.github/workflows/lib/pull-request-router.yml`
2. **Manual** — `gh workflow run dispatch.yml -R gardusig/cli -f workflow=…`
3. **CLI** — `cli pipeline run pull-request …` → `repository_dispatch` on `gardusig/cli`

## Catalog

See `index/devops/yaml/catalog.yaml` for registered workflow ids, lib paths, and dispatch types.

## History

`gardusig/pipelines` was renamed to **`gardusig/cli`**. The library submodule lives at **`index/devops/yaml/`**.
