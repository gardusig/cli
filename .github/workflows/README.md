# Workflow library

Reusable GitHub Actions workflows (formerly `gardusig/yaml`).

| Path | Purpose |
| --- | --- |
| `lib/` | `workflow_call` routers and shared lanes |
| `pull-request/` | Per-language PR gate configs |
| `dispatch.yml` | Manual router across catalog entries |
| `../config/ci/catalog.yaml` | Workflow registry |

App repos call `gardusig/cli/.github/workflows/lib/pull-request-router.yml@main`.
