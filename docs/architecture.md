# Architecture

From [issue #3](https://github.com/gardusig/cli/issues/3):

```
CLI → Command → Workflow / Service → Provider → External API
```

## Current implementation

- **`src/cli.py`** — Typer app, command registration
- **`src/commands/git.py`** — git subcommands (thin)
- **`src/services/git_shortcuts.py`** — git business logic + subprocess calls
- **`src/utils/process.py`** — `run_git` wrapper
- **`src/internal/read/`** — read-only inventory (worktree snapshot, operation classification)
- **`src/internal/write/`** — write gate with delimiter + Q&A before mutations
- **`src/utils/confirm.py`** — thin re-export of write gate helpers
- **`src/commands/{backup,restore,...}`** — placeholders for future workflows
- **`src/scripts/chrome/`** — bookmark export/import (issue #1)

Providers stay unimplemented until backup/sync issues land. Git operations use local `git` only.

## Verification

| Layer | Where it runs | Entry |
| --- | --- | --- |
| Unit (≥80% coverage, full pytest) | `cli:integration` container | `cli test python unit .` |
| Integration (full pytest, smoke, live docker) | `cli:integration` container | `cli test python integration .` |
| Integration (full pytest, smoke, public APIs, live docker) | same image + host socket | `cli test python integration .` |
| Local CLI usage | PyPI venv on host | `pip install gardusig-cli` |

Harness: `github-pipelines Docker stages` copies the repo to `/tmp/cli` inside an ephemeral container so git resets and fixtures never touch the host checkout. See [docker.md](docker.md).
