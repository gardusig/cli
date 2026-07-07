# Workflow library (`gardusig/yaml`)

## Model

| Layer | Location | Owns |
| --- | --- | --- |
| **Library** | `gardusig/yaml` (submodule: `index/devops/yaml/`) | Reusable `workflow_call` routers, `catalog.yaml`, hub images (`docker/operator`, `docker/cli-base`) |
| **App repo** | `gardusig/cli`, language repos, … | `Dockerfile`, `.github/pull-request.yaml`, thin `.github/workflows/pull-request.yml` caller |
| **App-specific automation** | Same app repo | `.github/workflows/test-nightly.yml`, `.github/release.yaml`, `.github/repo-review.yaml` |

## Triggers

1. **PR checks** — app `.github/workflows/pull-request.yml` → `workflow_call` → `gardusig/yaml/.github/workflows/lib/pull-request-router.yml`
2. **Manual** — `gh workflow run dispatch.yml -R gardusig/yaml -f workflow=…`
3. **CLI** — `cli pipeline run pull-request …` → `repository_dispatch` on `gardusig/yaml`

## Catalog

See `index/devops/yaml/catalog.yaml` for registered workflow ids, lib paths, and dispatch types.

## History

`gardusig/pipelines` was renamed to **`gardusig/yaml`**. The library submodule lives at **`index/devops/yaml/`**.
