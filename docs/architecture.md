# Architecture

From [issue #3](https://github.com/gardusig/python-cli/issues/3):

```text
CLI -> Command -> Workflow / Service -> Provider / Transport -> External API
```

## Current Implementation

- **`src/cli.py`** registers the Typer root app, visible public command groups, and hidden compatibility aliases such as `g`.
- **`src/commands/`** contains thin command adapters. Commands parse options, enforce write gates, and delegate behavior to services.
- **`src/services/`** owns business logic and stable JSON contracts, for example `git_shortcuts`, `gh_service`, `project_service`, `docker_runtime`, `notion_pairs`, and `test_packages`.
- **`src/providers/`** owns external process/API adapters, including GitHub CLI/API transports and GitHub Projects subprocess access.
- **`src/internal/write/`** owns write-gate confirmation for destructive or remote-mutating actions.
- **`src/internal/read/`** owns read-only repository inventory and operation classification helpers.
- **`src/services/toolkit/`** provides Python-native lint/test/structure/pipeline handlers that replaced the old repo-local shell script surface.

## Public Command Surface

The public CLI is intentionally registry-driven:

- `src/integration/public_endpoints.py` lists top-level command and endpoint checks.
- `src/integration/public_commands.py` verifies public command registry completeness.
- `src/services/test_packages.py` maps changed paths to package-specific test commands for local use and for `github-pipelines` consumers.
- `src/utils/catalog.py` drives `cli links` discoverability.

Hidden aliases and placeholders are allowed, but they should be intentional and documented when user-facing:

- `cli g ...` is a hidden alias for `cli git ...`.
- `cli backup ...`, `cli bookmarks ...`, and `cli publish ...` are compatibility/legacy surfaces.
- `cli restore` is a stable placeholder until restore workflow work lands.

## External Ownership

This repository owns Python application code, docs, fixtures, command registries, and deterministic test contracts. It does not own workflow YAML, Dockerfiles, compose files, schedules, or CI job graphs. Those remain in `gardusig/github-pipelines`.

## Verification

| Layer | Owner | Entry |
| --- | --- | --- |
| Focused package tests | this repo contract, pipeline execution | `cli test packages run PACKAGE` |
| Changed-path selection | this repo contract | `cli test packages resolve --base BASE --head HEAD` |
| Full-suite safety net contract | this repo contract | `cli test packages suite` |
| Unit / integration wrappers | Python handlers | `cli test python unit .`, `cli test python integration .` |
| Docker images and workflow jobs | `github-pipelines` | pipeline-owned Docker stages |

The Docker harness copies the repo into an ephemeral workspace so git resets and fixtures never touch the host checkout. See [docker.md](docker.md).
