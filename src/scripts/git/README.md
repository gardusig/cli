# Git scripts

Shell wrappers that delegate to `cli git <command>`.

| Script | CLI |
| --- | --- |
| `branch.sh` | `cli git branch list` |
| `branch-list.sh` | `cli git branch list` |
| `branch-current.sh` | `cli git branch current` |
| `branch-prune.sh` | `cli git branch prune` |
| `branch-rename.sh` | `cli git branch rename` |
| `branch-delete.sh` | `cli git branch delete` |
| `branch-delete-merged.sh` | `cli git branch delete --merged` |
| `branch-delete-all.sh` | `cli git branch delete --all` |
| `branch-clear.sh` | `cli git branch clear` |
| `cherry-pick.sh` | `cli git cherry pick` |
| `clean.sh` | `cli git clean` |
| `commit.sh` | `cli git commit` |
| `docs.sh` | `cli git docs` |
| `large-files.sh` | `cli git large files` |
| `main.sh` | `cli git main` |
| `post-merge-cleanup.sh` | `cli git post merge cleanup` |
| `pull.sh` | `cli git pull` |
| `push.sh` | `cli git push` |
| `reset.sh` | `cli git reset` |
| `rebase.sh` | `cli git rebase` |
| `revert.sh` | `cli git revert` |
| `review.sh` | `cli git review` |
| `start.sh` | `cli git start` |
| `stash.sh` | `cli git stash` |
| `tag.sh` | `cli git tag` |
| `zip.sh` | `cli git zip` |

Usage:

```bash
./src/scripts/git/commit.sh -m "wip"
./src/scripts/git/review.sh          # shell syntax + Docker unit tests
./src/scripts/git/review.sh --quick  # shell syntax only
```

Set `CLI_BIN` to override the cli executable.

Verification never runs host `pytest`; `review` delegates to `cli test python unit .` in Docker when not `--quick`.
