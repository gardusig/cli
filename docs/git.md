# Git commands

`cli git` wraps common local git workflows. Commit message defaults to `.`.

Each command has a shell wrapper under `src/scripts/git/`:

| Script | Command |
| --- | --- |
| `src/scripts/git/branch.sh` | `cli git branch list` |
| `src/scripts/git/branch-list.sh` | `cli git branch list` |
| `src/scripts/git/branch-current.sh` | `cli git branch current` |
| `src/scripts/git/branch-prune.sh` | `cli git branch prune` |
| `src/scripts/git/branch-rename.sh` | `cli git branch rename` |
| `src/scripts/git/branch-delete.sh` | `cli git branch delete` |
| `src/scripts/git/branch-delete-merged.sh` | `cli git branch delete --merged` |
| `src/scripts/git/branch-delete-all.sh` | `cli git branch delete --all` |
| `src/scripts/git/branch-clear.sh` | `cli git branch clear` |
| `src/scripts/git/cherry-pick.sh` | `cli git cherry pick` |
| `src/scripts/git/clean.sh` | `cli git clean` |
| `src/scripts/git/commit.sh` | `cli git commit` |
| `src/scripts/git/docs.sh` | `cli git docs` |
| `src/scripts/git/large-files.sh` | `cli git large files` |
| `src/scripts/git/main.sh` | `cli git main` |
| `src/scripts/git/post-merge-cleanup.sh` | `cli git post merge cleanup` |
| `src/scripts/git/pull.sh` | `cli git pull` |
| `src/scripts/git/push.sh` | `cli git push` |
| `src/scripts/git/rebase.sh` | `cli git rebase` |
| `src/scripts/git/reset.sh` | `cli git reset` |
| `src/scripts/git/revert.sh` | `cli git revert` |
| `src/scripts/git/review.sh` | `cli git review` |
| `src/scripts/git/start.sh` | `cli git start` |
| `src/scripts/git/stash.sh` | `cli git stash` |
| `src/scripts/git/tag.sh` | `cli git tag` |
| `src/scripts/git/deploy.sh` | `cli git deploy` |
| `src/scripts/git/tag-list.sh` | `cli git tag list` |
| `src/scripts/git/tag-push.sh` | `cli git tag push` |
| `src/scripts/git/zip.sh` | `cli git zip` |

## Internal read/write

Pattern:

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

### Tag naming (per repo)

Put [`config/tag.yaml`](../config/tag.yaml) in the target repo, or let the CLI **detect** the pattern from existing tags:

| `pattern` | Example | Default when omitted |
| --- | --- | --- |
| `semver-v` | `v0.1.0` | Used when `pyproject.toml` exists (this repo) |
| `semver` | `1.0.0` | — |
| `date` | `2026-06-24` | Daily snapshot repos |
| `plain` | `my-release` | No validation / no auto-suggest |

Optional keys: `bump` (`patch` \| `minor` \| `major`), `require_increase: true` (reject tags ≤ latest).

**This repo** (`config/tag.yaml`): `semver-v`, patch bump, `require_increase: true`.  
`cli git tag` with no name **auto-suggests the next tag** (e.g. `v0.1.0` → `v0.1.1`).

PR CI runs [`src/scripts/ci/version-check.sh`](../src/scripts/ci/version-check.sh) — `pyproject.toml` version must be **greater than** `main`.

```bash
cli pypi version suggest      # next package version (patch)
cli pypi version tag-suggest  # next git tag for current repo
cli pypi version check        # compare HEAD vs origin/main
```

```bash
cli git tag                    # sync main, suggest next vX.Y.Z, push to origin
cli git tag v0.1.1             # explicit release tag
cli git tag list               # local + remote tags (sorted)
cli git tag push               # push latest local tag to origin
cli git tag push v0.1.1 --yes --force   # force-push when remote differs
cli git zip                    # zip latest local tag → git-tags/REPO/
cli git zip v0.1.1 -o out.zip
```

`tag` syncs **main** first, creates the **next** tag greater than the latest (per `config/tag.yaml`), then pushes to `origin` when configured. `zip` always archives the **latest local** tag unless you pass a name. Subcommands: `list`, `push` (`--force`), and explicit tag names still work.

### CI/CD workflows

See [ci-workflows.md](ci-workflows.md) for the standard trio: **`test.yml`** (PR build/test) → **`deploy.yml`** (main → tag) → **`release.yml`** (tag → GitHub Release artifacts).

### Deploy (auto-tag on main)

When `main` has commits not covered by the latest policy tag and there are **no open PRs**, create and push the next tag:

```bash
cli git deploy --status     # read-only: main vs tag + open PR count
cli git deploy --dry-run    # same as --status
cli git deploy              # interactive write gate
cli git deploy --yes        # CI / automation
```

Push to `main` can trigger deploy via external CI, which calls `./src/scripts/git/deploy.sh --yes`. Open PRs block deploy unless you pass `--skip-pr-check`.

For multi-repo zip inventory and bulk ingest, use [`cli drive ingest`](drive.md).

Shell wrappers: `src/scripts/git/tag-list.sh`, `src/scripts/git/tag-push.sh`, `src/scripts/git/zip.sh`.

**Debug tests:** `cli test python unit .` (fast host pytest) · `cli test python integration .` (tags + Docker unit + integration).

## Review (workspace health)

```bash
cli git review
# or
./src/scripts/git/review.sh
```

Runs shell syntax checks; without `--quick`, also `cli test python unit .` (Docker — requires Docker Desktop). No commit or push. Use `cli git review --quick` when Docker is unavailable.

## Read-only introspection

No write gate:

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

Lists markdown paths for sync. In-place edits use `cli git docs`.
