# Task Configuration

Local setup:

```bash
cli config init
cli config secrets init
cli config set notion.task_root ~/git-local/private/private/tasks
cli config set notion.pairs_file tasks.pairs.json
cli config set gh.issues.repo gardusig/private
cli config check --tasks
```

`tasks/board.yaml` in `gardusig/private` stores non-secret targets such as the Notion database id and GitHub repo.

Secrets:

- local: `.env` or `~/.config/cli/secrets/*`
- CI: `gardusig/github-pipelines` secrets only

Do not put CI secrets in app repos.
