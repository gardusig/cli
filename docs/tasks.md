# Tasks (`cli tasks`)

Local task pair helpers around Notion sync.

## Commands

| Command | Purpose |
| --- | --- |
| `cli tasks pairs validate` | Check `tasks.pairs.json` against header/body files |
| `cli tasks pairs build` | Rebuild pairs manifest from task root |
| `cli tasks run notion deploy` | Shortcut for `cli notion deploy --yes` |
| `cli tasks run notion ingest` | Shortcut for `cli notion ingest` |
| `cli tasks ingest-pr --source notion` | Ingest, commit, push a sync branch |

## Configuration

Task paths live under **`notion.task_root`**. Runbook links use **`notion.link_repo`** (git-hosted `tasks/` tree).

```bash
cli configure check --tasks
```

## Related

- [notion.md](notion.md)
- [config-tasks.md](config-tasks.md)
