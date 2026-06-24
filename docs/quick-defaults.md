# Quick defaults

Cli favors **suggested values** over prompts so common flows are one command.

| Command | Default when omitted | Example |
| --- | --- | --- |
| `cli git start` | Prep + branch `wip-YYMMDD-NNN` or your slug | `cli git start issue-9-docker --yes` |
| `cli git commit` | Message `.` | `cli git commit` |
| `cli git push` | Add + commit + push; message `.` if dirty; on `main`, start random branch first | `cli git push --yes` |
| `cli git reset` | Return to synced main + prune merged branches | `cli git reset --yes` |
| `cli git reset --main-only` | Sync main only (no branch delete) | `cli git reset --yes --main-only` |
| `cli git stash push` | Message `.` | `cli git stash push` |
| `cli git tag` | Name `YYYY-MM-DD` (today) | `cli git tag` |
| `cli git zip` | Tag `YYYY-MM-DD` (today) | `cli git zip` → iCloud `git-tags/REPO/REPO-TAG.zip` |

## Branch names

`wip-260611-001`, `wip-260611-002`, … increment per day based on existing local branches. Pass an explicit name only when you care:

```bash
cli git start my-feature --no-prep
```

## Shell wrappers

Scripts under `scripts/git/` forward flags to the CLI and inherit the same defaults:

```bash
./scripts/git/start.sh          # auto branch name
./scripts/git/commit.sh         # message '.'
./scripts/git/large-files.sh    # see docs/large-files.md
```

Full index: `cli links` · [Git commands](git.md)
