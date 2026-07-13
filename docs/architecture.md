# Architecture

```
cli (Typer root)
  └── commands/     # Thin Typer apps per domain
  └── services/     # Business logic and stable contracts
  └── providers/    # External API/process adapters
  └── integration/  # Dockerized command-surface checks
```

- **`src/commands/`** parses argv, prints tables/JSON, calls services.
- **`src/services/`** owns workflows: `git_shortcuts`, `notion_sync`, `drive_sync`, `docker_runtime`, `test_packages`, etc.
- **`src/providers/`** wraps Notion, Drive, Chrome paths, OpenCode/DeepSeek HTTP.
- **`src/integration/`** registers every public command for mocked integration tests.

Git operations use the local **`git`** binary via `src/utils/process.run_git`.
