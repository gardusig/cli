# Tests

Pytest suite for `gardusig-cli`. Run via Docker only (see [docs/setup.md](../docs/setup.md)):

```bash
./scripts/test/unit.sh         # pytest -m "not integration" + ≥80% coverage
./scripts/test/integration.sh  # full pytest + smoke + live docker
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
| `chrome/` | Chrome bookmarks CLI + shell scripts, docker integration |
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
- `tests/integration/check_api_integration.py` — API workspaces (drive, gh, notion, chrome, pypi)
