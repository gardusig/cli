# Task configuration

```bash
cli config set notion.task_root ~/github/private/tasks
cli config set notion.link_repo gardusig/private
cli config set notion.pairs_file tasks.pairs.json
```

Validate:

```bash
cli configure check --tasks
cli tasks pairs validate
```
