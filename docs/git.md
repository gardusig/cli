# Git commands

`cli git` wraps common local git workflows. Commit message defaults to `.`.

Each command maps to a [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git) and has a shell wrapper under `scripts/git/`:

| Skill | Script | Command |
| --- | --- | --- |
| `@git-branch` | `scripts/git/branch.sh` | `cli git branch` |
| `@git-branch-delete` | `scripts/git/branch-delete.sh` | `cli git branch delete` |
| `@git-branch delete --merged` | `scripts/git/branch-delete-merged.sh` | `cli git branch delete --merged` |
| `@git-branch delete --all` | `scripts/git/branch-delete-all.sh` | `cli git branch delete --all` |
| `@git-branch-clear` | `scripts/git/branch-clear.sh` | `cli git branch clear` |
| `@git-cherry-pick` | `scripts/git/cherry-pick.sh` | `cli git cherry pick` |
| `@git-commit` | `scripts/git/commit.sh` | `cli git commit` |
| `@git-docs` | `scripts/git/docs.sh` | `cli git docs` |
| `@git-large-files` | `scripts/git/large-files.sh` | `cli git large files` |
| `@git-main` | `scripts/git/main.sh` | `cli git main` |
| `@git-post-merge-cleanup` | `scripts/git/post-merge-cleanup.sh` | `cli git post merge cleanup` |
| `@git-pull` | `scripts/git/pull.sh` | `cli git pull` |
| `@git-push` | `scripts/git/push.sh` | `cli git push` |
| `@git-rebase` | `scripts/git/rebase.sh` | `cli git rebase` |
| `@git-reset` | `scripts/git/reset.sh` | `cli git reset` |
| `@git-revert` | `scripts/git/revert.sh` | `cli git revert` |
| `@git-review` | `scripts/git/review.sh` | `cli git review` |
| `@git-start` | `scripts/git/start.sh` | `cli git start` |
| `@git-stash` | `scripts/git/stash.sh` | `cli git stash` |
| `@git-tag` | `scripts/git/tag.sh` | `cli git tag` |
| `@git-tag-list` | `scripts/git/tag-list.sh` | `cli git tag list` |
| `@git-tag-push` | `scripts/git/tag-push.sh` | `cli git tag push` |
| `@git-zip` | `scripts/git/zip.sh` | `cli git zip` |

## Internal read/write

Pattern mirrors [cursor-skills internal read/write](https://github.com/gardusig/cursor-skills/tree/main/skills/internal):

1. **Read** (`src/internal/read/`) — worktree snapshot, no prompts
2. **Write gate** (`src/internal/write/gate.py`) — prints `--- cli write gate ---` with repo context, then asks to proceed
3. **Write** — mutation runs only after `--yes` or interactive confirmation

Read-only commands (`review`, `docs`, `branch list`, `stash list`) skip the gate.

## Safety gates

Operations that mutate remote state or discard local work require confirmation:

| Operation | Confirmation |
| --- | --- |
| `git push` | `--yes` or interactive prompt (shows branch + intent summary) |
| `git reset` | `--yes` or interactive prompt (commits dirty branch work by default) |
| `git main` (align main only) | `--yes` or interactive prompt |
| `git branch delete` | `--yes` or interactive prompt |
| `git branch clear` | `--yes` or interactive prompt; optional second prompt for remote branches |
| `git stash drop/clear` | `--yes` or interactive prompt |
| `git tag --push` | `--yes` or interactive prompt |

No confirmation needed:

- `git commit`
- `git start --no-prep` (creates branch from current state)
- `git pull`
- `git stash push/list/apply/pop`

## Start a branch

Default (issue workflow — align main + branch):

```bash
cli git start issue-9-docker --yes
```

Branch from the **current** working tree without reset/clean:

```bash
cli git start my-feature --no-prep
```

## Return to synced main

```bash
cli git reset --yes              # checkout main, fetch, pull, clean
cli git reset --yes --delete-merged  # sync main + delete merged branches
cli git reset --yes --main-only  # sync main only (skip branch prompt)
cli git reset --yes --discard    # drop uncommitted work on current branch
```

On a feature branch with uncommitted edits, `reset` commits with `.` (or `-m`) before checking out `main`. Then it fetches `upstream` / `fork` / `origin`, hard-resets `main` to the newest tip among those refs, and cleans the worktree.

`git pull` on `main` does the same sync. On a feature branch it merges tracking upstream (when set) and the newest main tip.

## Publish

```bash
cli git push              # interactive: branch summary → add + commit + push
cli git push --yes        # non-interactive
cli git commit -m "wip"   # commit only (no push)
```

`push` shows a write gate with branch, dirty state, commit message, and intent (`add → commit → push`) before running. On `main`, it starts a random branch first unless you pass `--allow-main`.

## Branch delete

`branch delete --merged` removes branches merged into main (lists local + remote in the prompt):

```bash
cli git branch delete --merged
cli git branch delete --merged --yes
```

`branch delete --all` deletes **every** branch except `main`, including unmerged work (local + remote):

```bash
cli git branch delete --all
cli git branch delete --all --yes
```

## Clear all branches (nuclear local reset)

`branch clear` resets the working tree, then deletes all local branches except `main`:

```bash
cli git branch clear
```

1. Write gate — confirms hard reset + clean, checkout `main`, delete **every** local branch except `main` (lists branches in the prompt).
2. Second prompt — optionally delete all remote branches on `origin` except `main` (default: keep remotes).

Non-interactive full wipe:

```bash
cli git branch clear --yes --delete-remote
```

## Tag and zip

Single-repository only (run from the repo you want to tag).

```bash
cli git tag                    # sync main, create today's tag, push to origin
cli git tag 2026-06-11         # named tag
cli git tag list               # local + remote tags (sorted)
cli git tag push               # reconcile today's tag with origin
cli git tag push 2026-06-11 --yes
cli git tag 2026-06-11 --yes --force   # replace local tag / force-push remote
cli git zip                    # zip today's tag → git-tags/REPO/REPO-TAG.zip (iCloud)
cli git zip 2026-06-11 -o out.zip
```

`tag` syncs **main** first (same as `git reset`), creates an annotated tag on the latest main commit, then pushes to `origin` when configured. Default tag name is **today's date** (`YYYY-MM-DD`). Pass `--yes` if the worktree is dirty. Pass `--force` to replace an existing local tag or force-push when the remote tag differs.

For multi-repo zip inventory and bulk ingest, use [`cli drive ingest`](drive.md).

Shell wrappers: `scripts/git/tag-list.sh`, `scripts/git/tag-push.sh`, `scripts/git/zip.sh`.

## Review (workspace health)

```bash
cli git review
# or
./scripts/git/review.sh
```

Runs shell syntax checks; without `--quick`, also `./scripts/test/unit.sh` (Docker — requires Docker Desktop). No commit or push. Use `cli git review --quick` when Docker is unavailable.

## Read-only introspection (cursor-skills)

Used by [`read-cli-git`](https://github.com/gardusig/cursor-skills/blob/main/skills/internal/read/cli/git/SKILL.md) — no write gate:

```bash
cli git branch current
cli git diff stat --base upstream/main
cli git diff names --base "$BASE_GIT"
cli git log oneline --base "$BASE_GIT"
cli git log messages --base "$BASE_GIT" --max-count 30
cli git rev-list count --base "$BASE_GIT"
cli git remote url upstream
cli git rev parse HEAD
cli git merge-base check --base "$BASE_GIT"
cli git publish check --remote origin --branch feature-x
```

## Docs inventory

```bash
cli git docs
```

Lists markdown paths for sync. In-place edits use cursor-skills `@git-docs`.
