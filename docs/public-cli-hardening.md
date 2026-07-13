# Public CLI hardening

Every public command is listed in:

| Module | Role |
| --- | --- |
| [`src/integration/public_endpoints.py`](../src/integration/public_endpoints.py) | Top-level + `cli git` + `cli pypi` checks |
| [`src/integration/cli_api_checks.py`](../src/integration/cli_api_checks.py) | Mocked notion/drive/chrome API checks |
| [`src/integration/integration_coverage.py`](../src/integration/integration_coverage.py) | Inventory gate (ok + fail per path) |

## Gates

```bash
python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
```

## Write policy

Destructive operations require `cli … --yes` via `src/internal/write/gate.py`. Git push, tag, drive deploy, notion deploy, and PyPI upload are gated.
