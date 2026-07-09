# Configure

`cli configure` is the single configuration entry point. It works like `aws configure` or `git config`: install the package, then set values by key.

## Install

```bash
pip install gardusig-cli
```

## Common Commands

```bash
cli configure list
cli configure set notion.token secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
cli configure set gh.token --stdin
cli configure get notion.token
cli configure import-env
cli configure check --tasks
```

Secret values are masked by default. Use `--show` only when you intentionally need to inspect a local value.

## Resolution Order

1. Environment variable, such as `NOTION_TOKEN`
2. Value previously stored with `cli configure set`
3. Clear error with the key and environment variable to set

CI and Docker should inject GitHub secrets as environment variables, then run:

```bash
cli configure import-env
cli configure check --tasks
```

Use `--persist` with `import-env` only when you intentionally want to write token files in the current config directory.

## Keys

| Key | Environment | Example |
|-----|-------------|---------|
| `notion.token` | `NOTION_TOKEN` | `secret_...` |
| `gh.token` | `GH_TOKEN` | `ghp_...` |
| `pypi.token` | `PYPI_API_TOKEN` | `pypi-...` |
| `notion.database_id` | `NOTION_DATABASE_ID` | Notion database id |
| `notion.task_root` | `NOTION_TASK_ROOT` | `/workspace/tasks` |
| `gh.issues.repo` | | `gardusig/private` |

The full credential manifest lives at `config/secrets.manifest.yaml`.
