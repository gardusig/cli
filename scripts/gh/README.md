# GitHub (`gh`) scripts

Shell wrappers for `cli gh` commands. Each script delegates to `cli gh <command>`.

| Script | CLI |
| --- | --- |
| `backlog-next.sh` | `cli gh backlog next` |
| `backlog-tree.sh` | `cli gh backlog tree` |
| `backlog-resequence.sh` | `cli gh backlog resequence` |
| `issue-list.sh` | `cli gh issue list` |
| `issue-view.sh` | `cli gh issue view` |
| `issue-context.sh` | `cli gh issue context` |
| `issue-search.sh` | `cli gh issue search` |
| `issue-create.sh` | `cli gh issue create` |
| `issue-edit.sh` | `cli gh issue edit` |
| `issue-close.sh` | `cli gh issue close` |
| `issue-comment.sh` | `cli gh issue comment` |
| `issue-batch.sh` | `cli gh issue batch` |
| `label-list.sh` | `cli gh label list` |
| `sync-labels.sh` | `cli gh label sync` (manifest) |
| `labelize-backlog.sh` | `cli gh issue batch` (backlog-labelize.batch.yaml) |
| `pr-list.sh` | `cli gh pr list` |
| `pr-view.sh` | `cli gh pr view` |
| `pr-diff.sh` | `cli gh pr diff` |
| `pr-create.sh` | `cli gh pr create` |
| `pr-edit.sh` | `cli gh pr edit` |
| `pr-close.sh` | `cli gh pr close` |
| `pr-merge.sh` | `cli gh pr merge` (blocked — exits 1) |
| `project.sh` | `cli gh project` (blocked — exits 1) |
| `ruleset.sh` | `cli gh ruleset` (blocked — exits 1) |
| `repo-view.sh` | `cli gh repo view` |

## PR path (granular)

```bash
./scripts/gh/backlog-next.sh --format json
./scripts/git/reset.sh --yes --main-only
./scripts/git/start.sh issue-42-slug --yes
# … work …
./scripts/git/push.sh --yes
./scripts/git/review.sh
./scripts/gh/pr-create.sh --title "." --body "" --yes
# merge in GitHub UI — pr-merge.sh is blocked by policy
./scripts/gh/issue-close.sh 42 --comment "Done" --yes
./scripts/git/reset.sh --yes --delete-merged
```

See [docs/workflows.md](../docs/workflows.md) and [docs/gh.md](../docs/gh.md).

Set `CLI_BIN` to override the cli executable.
