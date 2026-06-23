# Integration check entry points

Python runners invoked from `scripts/integration-smoke.sh` and `scripts/docker/run-*.sh`.
Implementation lives in `cli/integration/`; these files are thin `main()` wrappers.

| Script | Purpose |
| --- | --- |
| `check_integration_coverage.py` | Registry gate: every public command has ok/fail checks |
| `check_public_commands.py` | Run all public CLI integration checks |
| `check_public_endpoints.py` | Run all endpoint checks |
| `check_workflow_integration.py` | Git workflow scenarios |
| `check_api_integration.py` | Pytest API integration modules |
| `check_docker_commands.py` | Docker CLI checks (`--live` for host daemon) |
| `check_notion_tasks.py` | Alias → `check_api_integration.py` |

```bash
python tests/integration/check_integration_coverage.py
python tests/integration/check_public_commands.py
```
