# Workflow library (`gardusig/yaml`)

## Model

| Layer | Location | Owns |
| --- | --- | --- |
| **Library** | `gardusig/yaml` (submodule: `quickstart/yaml/`) | Reusable `workflow_call` routers, `catalog.yaml`, hub images (`docker/operator`, `docker/cli-base`) |
| **App repo** | `gardusig/cli`, language repos, … | `Dockerfile`, `.github/pull-request.yaml`, thin `.github/workflows/pull-request.yml` caller |
| **App-specific automation** | Same app repo | `.github/workflows/test-nightly.yml`, `.github/release.yaml`, `.github/repo-review.yaml` |

## Triggers

1. **PR checks** — app `.github/workflows/pull-request.yml` → `workflow_call` → `gardusig/yaml/.github/workflows/lib/pull-request-router.yml`
2. **Manual** — `gh workflow run dispatch.yml -R gardusig/yaml -f workflow=…`
3. **CLI** — `cli pipeline run pull-request …` → `repository_dispatch` on `gardusig/yaml`

## Catalog

See `quickstart/yaml/catalog.yaml` for registered workflow ids, lib paths, and dispatch types.

## Migration from `gardusig/pipelines`

- Hub renamed conceptually to **`gardusig/yaml`**
- Nested under **`quickstart/yaml/`** git submodule
- Per-repo Dockerfiles live in each app repo root
- Repo-specific workflows (nightly, main release, repo-review) moved into owning repos

Create the GitHub repo `gardusig/yaml` from `quickstart/yaml/` (or `/home/gardusig/github/public/yaml`) and enable redirects from `gardusig/pipelines` if renaming.
