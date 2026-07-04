# scripts/

**Reusable shell implementation** — invoked by `cli` commands and by external CI runners.

This directory is *how* each step runs. Orchestration (what runs, in what order, GitHub events) lives outside this repository.

| Directory | Purpose |
| --- | --- |
| `git/` | Git shortcuts (`cli git …`) |
| `gh/` | GitHub shortcuts (`cli gh …`) |
| `craft/` | Thin wrappers → `cli opencode gh` |
| `drive/`, `chrome/`, `notion/` | Domain-specific ops |
| `deploy/`, `release/` | Deploy and release helpers |
| `ci/` | Version and policy checks |

Python code: [`src/`](../src/). Integration checks: [`tests/integration/`](../tests/integration/).
