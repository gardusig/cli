# Tests

Pytest suite for `gardusig-cli`. Run via Docker only (see [docs/setup.md](../docs/setup.md)):

```bash
cli test python unit .
cli test python integration .
```

## Layout

| Path | Purpose |
| --- | --- |
| `conftest.py` | Shared fixtures; deselects `@pytest.mark.integration` on host |
| `constants.py` | `ROOT` — repository root path |
| `fixtures/` | Static fixture data (notion tasks, bookmarks, contest toy, …) |
| `harness/` | Shared test helpers (`drive_harness`, `gh_harness`, …) |
| `integration/` | **Gate runners** (`check_*.py`) invoked by smoke/unit scripts — not pytest modules |
| `backup/` | Backup repository, zip, encrypt, replica deploy |
| `drive/` | Drive CLI, sync engine, docker integration |
| `docker/` | Docker CLI, runtime, guard, CI harness checks |
| `git/` | Git CLI, shortcuts service, workflow, integration scenarios |
| `gh/` | GitHub CLI, service, provider, docker integration |
| `notion/` | Notion CLI, sync, pairs/markdown, docker integration |
| `chrome/` | Chrome bookmarks CLI + docker integration |
| `pypi/` | PyPI CLI, unit helpers, build integration |
| `contest/` | Contest CLI, runner, validate integration |
| `cli/` | Cross-cutting CLI (help, endpoints, links, API integration) |
| `internal/` | Read/write gate internals |
| `meta/` | Hygiene, coverage gates, public-command registries, utils |

## Naming

- `test_*.py` under domain folders — normal pytest modules (discovered recursively).
- `tests/integration/check_*.py` — standalone scripts that validate public CLI coverage; do not confuse with `test_*_integration.py` pytest files.

## Public CLI coverage

Integration gates ensure every public command has refuse + success checks:

- `tests/integration/check_integration_coverage.py` — registry completeness
- `tests/integration/check_public_endpoints.py` — git endpoints
- `tests/integration/check_public_commands.py` — all public commands
- `tests/integration/check_package_integration.py` — per-package selective CI legs
- `tests/integration/check_api_integration.py` — full API workspaces (or `--package gh`)

## Selective CLI Packages

`src/services/test_packages.py` maps changed repo-relative paths to the CLI package tests
that should run first. It is the prerequisite for per-package scripts and selective PR CI.

```bash
cli test packages resolve --changed-path src/commands/gh.py --format json
cli test packages resolve --changed-path src/cli.py --format table
cli test packages run gh --dry-run --format table
cli test packages run gh --no-unit --dry-run --format json
cli test packages suite --format json
scripts/test/gh.sh --dry-run
scripts/test/pypi.sh --dry-run
scripts/test/all.sh
```

Examples:

- `src/commands/gh.py` resolves to `gh`, with `tests/gh/` and GitHub API checks.
- `src/cli.py` resolves to the broad `cli` package, so run command-surface checks and the full unit suite before merging.
- `pyproject.toml` resolves to `pypi`, covering packaging-sensitive tests.
- `src/providers/opencode.py` resolves to `opencode` and is marked `costs_api_tokens=true`; do not call paid AI commands from deterministic test selection.

`gardusig/github-pipelines` owns workflow YAML, Dockerfiles, schedules, and job
graphs. This repo owns the stable package registry and command contract:

- `cli test packages list` exposes all packages.
- `cli test packages resolve --base BASE --head HEAD` maps a PR diff to packages.
- `cli test packages run PACKAGE` runs one package locally or prints the command contract with `--dry-run`; use `--no-unit` for integration-only pipeline legs.
- `cli test packages suite` describes the full-suite safety net for nightly/manual pipeline runs.

### Per-package scripts (#82)

Nine shell wrappers under `scripts/test/` cover packages with Docker integration legs.
All other registry packages use `cli test packages run PKG` directly. See
[`scripts/test/README.md`](../scripts/test/README.md).
