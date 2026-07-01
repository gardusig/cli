# scripts/

**Reusable shell implementation** — invoked by `cli` commands and by `gardusig/pipelines` sequences.

Orchestration (what runs, in what order, GitHub events) lives in **[gardusig/pipelines](https://github.com/gardusig/pipelines)**. This directory is *how* each step runs.

| Directory | Purpose | Pipeline domain |
| --- | --- | --- |
| `test/` | Docker test harness (`unit.sh`, `integration.sh`, `all.sh`, …) | `ci/test` |
| `deploy/` | Deploy script | `ci/deploy` |
| `release/` | Release build | `ci/release` |
| `docker/` | Image build, in-container runners | used by test/deploy |
| `git/` | Git shortcuts (`cli git …`) | `git/*`, `issue/*`, `pr/*` |
| `gh/` | GitHub shortcuts (`cli gh …`) | `issue/*`, `pr/*`, `plan/*` |
| `craft/` | Thin wrappers → `cli opencode gh` | `issue/*`, `pr/*` |
| `pypi/`, `drive/`, `chrome/`, `notion/` | Domain-specific ops | ad hoc |

Python code: [`src/`](../src/). Integration checks: [`tests/integration/`](../tests/integration/).

```bash
# scripts are not workflows — pipelines calls them:
# sequences/ci/test.pipeline.yaml → run: ./scripts/test/unit.sh
```
