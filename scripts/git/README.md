# Git scripts

Shell wrappers for each [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git). Each script delegates to `cli git <command>`.

| Script | cursor-skills skill | CLI |
| --- | --- | --- |
| `branch.sh` | `git/branch` | `cli git branch` |
| `branch-delete.sh` | `git/branch/delete` | `cli git branch-delete` |
| `branch-delete-all.sh` | `git/branch/delete/all` | `cli git branch-delete-all` |
| `branch-clear.sh` | `git/branch/clear` | `cli git branch-clear` |
| `cherry-pick.sh` | `git/cherry/pick` | `cli git cherry-pick` |
| `commit.sh` | `git/commit` | `cli git commit` |
| `docs.sh` | `git/docs` | `cli git docs` |
| `large-files.sh` | `git/large/files` | `cli git large-files` |
| `main.sh` | `git/main` | `cli git main` |
| `post-merge-cleanup.sh` | `git/post/merge/cleanup` | `cli git post-merge-cleanup` |
| `pull.sh` | `git/pull` | `cli git pull` |
| `push.sh` | `git/push` | `cli git push` |
| `reset.sh` | `git/reset` | `cli git reset` |
| `rebase.sh` | `git/rebase` | `cli git rebase` |
| `reset.sh` | `git/reset` | `cli git reset` |
| `revert.sh` | `git/revert` | `cli git revert` |
| `review.sh` | `git/review` | `cli git review` |
| `start.sh` | `git/start` | `cli git start` |
| `stash.sh` | `git/stash` | `cli git stash` |
| `tag.sh` | `git/tag` | `cli git tag` |
| `zip.sh` | `git/zip` | `cli git zip` |

Usage:

```bash
./scripts/git/commit.sh -m "wip"
./scripts/git/review.sh          # shell syntax + Docker unit tests
./scripts/git/review.sh --quick  # shell syntax only
```

Set `CLI_BIN` to override the cli executable.

Verification never runs host `pytest`; `review` delegates to `./scripts/test-unit.sh` in Docker when not `--quick`.
