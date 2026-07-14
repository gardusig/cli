# Configure (`cli configure`)

AWS / git-style configuration: bootstrap once, then set keys individually.

## First run

```bash
cli configure init
cli configure list
cli configure set notion.task_root ~/github/private/tasks
cli configure set notion.token --stdin
cli configure check --tasks
```

`cli configure` with no subcommand runs `init` (creates `auth.yaml` + `secrets/`).

`cli configure path` prints the active config directory (XDG on Linux, Application Support on macOS).

Optional starter paths file:

```bash
cli configure init --example   # copies config.example.yaml → config.yaml
```

## Commands

| Command | Purpose |
| --- | --- |
| `init` | Create config dir, `auth.yaml`, `secrets/` |
| `set <key> [value]` | Write `config.yaml` or a token file (`--stdin` for secrets) |
| `get <key>` | Read a key (`--show` for secret values) |
| `unset <key>` | Remove a key or token file |
| `list` | Show which keys are set (`--json`) |
| `import-env [--persist]` | Import credentials from environment |
| `check --tasks` / `--pypi` | Validate a feature area |
| `path` | Print config directory |

## Common keys

| Key | Purpose |
| --- | --- |
| `backup.tags_dir` | Local git-tag zip folder |
| `notion.database_id` | Notion board |
| `notion.task_root` | Local `header/` + `body/` tree |
| `notion.link_repo` | `owner/repo` for runbook URLs |
| `chrome.bookmarks_file` | Bookmarks HTML backup |
| `notion.token` | Notion integration token (secret) |

See [configuration.md](configuration.md) and [secrets.md](secrets.md).

## Contributors

Tests and CI use `CLI_CONFIG_DIR=tests/fixtures/config` + `CLI_PROFILE=test` — not your home directory.
