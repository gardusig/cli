# Task Configuration

Local setup:

```bash
cli config init
cli config secrets init
cli config set notion.task_root ~/github/private/database/tasks
cli config set notion.pairs_file tasks.pairs.json
cli config set gh.issues.repo gardusig/database
cli config check --tasks
```

`tasks/board.yaml` in `gardusig/database` stores non-secret targets such as the Notion database id and GitHub repo.

Secrets:

- local: `.env` or `~/.config/cli/secrets/*`
- CI: `gardusig/gardusig/yaml` secrets only

Do not put CI secrets in app repos.
