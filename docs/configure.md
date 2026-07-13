# Configure (`cli configure`)

Unified configuration for paths and secrets.

## Secrets

```bash
cli configure list
cli configure set notion.token --stdin
cli configure import-env --persist
cli configure check --tasks
cli configure check --pypi
```

## Task paths

| Key | Purpose |
| --- | --- |
| `notion.database_id` | Notion board |
| `notion.task_root` | Local `header/` + `body/` tree |
| `notion.link_repo` | `owner/repo` for runbook URLs |
| `notion.labels_manifest` | Optional labels YAML beside tasks |

See [configuration.md](configuration.md) and [secrets.md](secrets.md).
