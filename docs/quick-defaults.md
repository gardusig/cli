# Quick defaults

Cli favors **suggested values** over prompts so common flows are one command.

| Command | Default when omitted | Example |
| --- | --- | --- |
| `cli git start` | Prep + branch `wip-YYMMDD-NNN` or your slug | `cli git start issue-9-docker --yes` |
| `cli git commit` | Message `.` | `cli git commit` |
| `cli git push` | Add + commit + push; message `.` if dirty; on `main`, start random branch first | `cli git push --yes` |
| `cli gh pr` | Title `.`, empty body, push first when needed | `cli gh pr --yes` |
| `cli gh wf run <workflow.yml>` | Repo from `-R` or `gh` default context | `cli gh wf run dispatch.yml -R gardusig/cli -f workflow=pull-request …` |
| `cli gh wf run failed <id>` | Failed-step logs (`gh run view --log-failed`) | `cli gh wf run failed 29015588872 -R gardusig/private` |
| `cli git reset` | Return to synced main; optional `--delete-merged` or interactive branch cleanup | `cli git reset --yes` |
| `cli git reset --main-only` | Sync main only (skip branch prompt) | `cli git reset --yes --main-only` |
| `cli git stash push` | Message `.` | `cli git stash push` |
| `cli git tag` | Next tag per `config/tag.yaml` or detection (e.g. `v0.1.1`) | `cli git tag` |
| `cli git zip` | Latest **local** tag for repo pattern | `cli git zip` |

## Branch names

`wip-260611-001`, `wip-260611-002`, … increment per day based on existing local branches. Pass an explicit name only when you care:

```bash
cli git start my-feature --no-prep
```

Full index: `cli links` · [Git commands](git.md)
