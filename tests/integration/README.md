# Integration tests

Integration is a **read-only smoke script** against the installed `cli` binary.

## Run locally

```bash
pip install -e .
export CLI_PROFILE=test
bash scripts/pull-request/integration-smoke.sh
```

Or the full dev integration leg (install + smoke):

```bash
bash scripts/pull-request/integration-test.sh
```

## What it checks

- `cli --help`, `cli --version`, basic help surfaces
- Disposable git repo via `CLI_GIT_ROOT`: `cli git branch`, `cli git log`, `cli git diff`
- Read-only GitHub policy: `cli gh policy list`, blocked `cli gh issue close`

## Legacy entry points

- `tests/integration/check_integration_coverage.py` — stub gate (smoke is source of truth)
- `tests/integration/check_public_commands.py` — runs `integration-smoke.sh`
