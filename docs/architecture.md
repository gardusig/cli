# Architecture

From [issue #3](https://github.com/gardusig/cli/issues/3):

```
CLI → Command → Workflow / Service → Provider → External API
```

## Current implementation

- **`gardusig_cli/cli.py`** — Typer app, command registration
- **`gardusig_cli/commands/git.py`** — git subcommands (thin)
- **`gardusig_cli/services/git_shortcuts.py`** — git business logic + subprocess calls
- **`gardusig_cli/utils/process.py`** — `run_git` wrapper
- **`gardusig_cli/internal/read/`** — read-only inventory (worktree snapshot, operation classification)
- **`gardusig_cli/internal/write/`** — write gate with delimiter + Q&A before mutations
- **`gardusig_cli/utils/confirm.py`** — thin re-export of write gate helpers
- **`gardusig_cli/commands/{backup,restore,...}`** — placeholders for future workflows
- **`scripts/chrome/`** — bookmark export/import (issue #1)

Providers stay unimplemented until backup/sync issues land. Git operations use local `git` only.

## Verification

| Layer | Where it runs | Entry |
| --- | --- | --- |
| Unit (≥80% coverage, full pytest) | `cli:integration` container | `./scripts/test/unit.sh` |
| Integration (full pytest, smoke, live docker) | `cli:integration` container | `./scripts/test/integration.sh` |
| Integration (full pytest, smoke, public APIs, live docker) | same image + host socket | `./scripts/test/integration.sh` |
| Local CLI usage | host `.venv` or PyPI venv | `./scripts/install-pypi.sh`, `./scripts/bootstrap.sh`, `./scripts/install.sh` |

Harness: `scripts/docker/common.sh` copies the repo to `/tmp/cli` inside an ephemeral container so git resets and fixtures never touch the host checkout. See [docker.md](docker.md).
