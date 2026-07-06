# Integration check entry points

Python runners invoked from the `cli test python ...` command surface.
Implementation lives in `src/integration/`; these files are thin `main()` wrappers.

**Docker only** — each script calls `require_docker_integration()` and exits on the host.
Use `cli test python unit .` or `cli test python integration .`, not bare `python tests/integration/...`.

| Script | Purpose |
| --- | --- |
| `check_integration_coverage.py` | Registry gate: every public command has ok/fail checks |
| `check_public_commands.py` | Run all public CLI integration checks |
| `check_public_endpoints.py` | Run all endpoint checks |
| `check_workflow_integration.py` | Git workflow scenarios (granular) |
| `check_workflows.py` | E2E workflow integration (plan, context, PR, reset) |
| `check_api_integration.py` | Pytest API integration modules |
| `check_docker_commands.py` | Docker CLI checks (`--live` for host daemon) |
| `check_notion_tasks.py` | Alias → `check_api_integration.py` |

**Config isolation** (workflow E2E): default `CLI_CONFIG_DIR=config/ci`; per-workflow overrides via `tests/fixtures/workflows/<name>/config.yaml`. GH calls use mocked stateful store (`tests/harness/gh_harness.py`).

Host cleanup after accidental local runs:

```bash
cli git clean --yes
```
