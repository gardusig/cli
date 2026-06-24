# Integration check entry points

Python runners invoked from `scripts/test/smoke.sh` and `scripts/docker/run-*.sh`.
Implementation lives in `gardusig_cli/integration/`; these files are thin `main()` wrappers.

**Docker only** — each script calls `require_docker_integration()` and exits on the host.
Use `./scripts/test/unit.sh` or `./scripts/test/integration.sh`, not bare `python tests/integration/...`.

| Script | Purpose |
| --- | --- |
| `check_integration_coverage.py` | Registry gate: every public command has ok/fail checks |
| `check_public_commands.py` | Run all public CLI integration checks |
| `check_public_endpoints.py` | Run all endpoint checks |
| `check_workflow_integration.py` | Git workflow scenarios |
| `check_api_integration.py` | Pytest API integration modules |
| `check_docker_commands.py` | Docker CLI checks (`--live` for host daemon) |
| `check_notion_tasks.py` | Alias → `check_api_integration.py` |

Host cleanup after accidental local runs:

```bash
./scripts/clean-local.sh
```
