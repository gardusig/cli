# Git commands

`cli git` wraps common local git workflows. Commit message defaults to `.`.

Core commands:

| Command | Purpose |
| --- | --- |
| `cli ship` | stage, commit (`.`), push `main` — personal backup flow |
| `cli git start` | align main and create a branch |
| `cli git push` | add, commit, and push current work |
| `cli git reset` | return to synced main and optionally clean branches |
| `cli git branch ...` | branch listing, pruning, deletion, and cleanup |
| `cli git tag ...` | tag, list, push, and suggest release tags |
| `cli git zip` | archive the latest or requested tag |
| `cli git review` | run command-surface and unit gates |

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
| `ship` | `--yes` or interactive prompt |
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

### Ship to main (default personal flow)

One entry point — no PR branch, no wip branch:

```bash
cli ship              # interactive write gate
cli ship --yes        # stage all, commit '.', push origin/main
cli s --yes           # hidden alias
```

Requires checkout on `main`. For feature branches use `cli git push`.

### Push (feature branches + optional wip flow)

```bash
cli git push              # interactive: branch summary → add + commit + push
cli git push --yes        # non-interactive
cli git commit -m "wip"   # commit only (no push)
```

`push` shows a write gate with branch, dirty state, commit message, and intent before running:

| Current state | Behavior |
| --- | --- |
| Feature branch with `origin` | `git add -A`, commit if dirty, push `origin HEAD` |
| `main` with `origin` (default) | commit if dirty and push `main` directly |
| `main` with `--branch` and `origin` | create a generated `wip-YYMMDD-NNN` branch, commit if dirty, push that branch |
| `main` with `--no-allow-main` and `origin` | same as `--branch` (wip flow) |
| No `origin` remote | commit local work only and report that nothing was pushed |
| `main` without `origin` | commit on `main` locally after confirmation (no push target) |
| Detached HEAD | refused before the write gate (`Cannot push from detached HEAD`) |

On `main` with `origin`, an interactive `cli git push --branch` may ask whether to push directly to `main` instead of starting a wip branch. Non-interactive runs use the flags you pass (`--branch` → wip flow; default → push `main`).

Before the write gate, `push` may surface **warnings** (informational; they do not block unless you decline the gate):

| Warning | When |
| --- | --- |
| `on main but upstream tracks '…'` | `--allow-main` on `main` and upstream is not `main` |
| `branch '…' is already merged into main` | current branch is merged into `main` |
| `branch '…' has no upstream` | `origin` exists but the branch has no tracking ref |

```bash
cli git push --yes --format json   # structured result: branch, pushed, remote, warnings, …
```

The no-remote case avoids failing late after staging/committing. Add a remote and rerun `cli git push --yes` when you are ready to publish.

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

Put `<repo>/config/tag.yaml` in the target repo (see [`src/data/config/tag.yaml.example`](../src/data/config/tag.yaml.example)), or let the CLI **detect** the pattern from existing tags:

| `pattern` | Example | Default when omitted |
| --- | --- | --- |
| `semver` | `1.0.0` | Used when `pyproject.toml` exists (this repo) |
| `semver-v` | `v0.1.0` | Legacy `v`-prefixed repos |
| `date` | `2026-06-24` | Daily snapshot repos |
| `plain` | `my-release` | No validation / no auto-suggest |

Optional keys: `bump` (`patch` \| `minor` \| `major`), `require_increase: true` (reject tags ≤ latest).

**This repo** uses bare semver tags with auto-detection when no `config/tag.yaml` is present.  
`cli git tag` with no name **auto-suggests the next tag** (e.g. `0.1.0` → `0.1.1`).

PR CI runs `cli pypi version check` — `pyproject.toml` version must be **greater than** `main`.

```bash
cli pypi version suggest      # next package version (patch)
cli pypi version tag-suggest  # next git tag for current repo
cli pypi version check        # compare HEAD vs origin/main
```

```bash
cli git tag                    # sync main, suggest next X.Y.Z, push to origin
cli git tag 0.1.1              # explicit release tag
cli git tag list               # local + remote tags (sorted)
cli git tag push               # push latest local tag to origin
cli git tag push 0.1.1 --yes --force   # force-push when remote differs
cli git zip                    # zip latest local tag → git-tags/REPO/
cli git zip 0.1.1 -o out.zip
```

`tag` syncs **main** first, creates the **next** tag greater than the latest (per `config/tag.yaml`), then pushes to `origin` when configured. `zip` always archives the **latest local** tag unless you pass a name. Subcommands: `list`, `push` (`--force`), and explicit tag names still work.

### CI/CD workflows

See [ci-workflows.md](ci-workflows.md): PR pipeline (`pull-request.yaml`) and tag-driven release (`release.yaml`).

### Deploy (auto-tag on main)

When `main` has commits not covered by the latest policy tag and there are **no open PRs**, create and push the next tag:

```bash
cli git deploy --status     # read-only: main vs tag + open PR count
cli git deploy --dry-run    # same as --status
cli git deploy              # interactive write gate
cli git deploy --yes        # CI / automation
```

Push to `main` can trigger deploy via external CI, which calls `cli git deploy --yes`. Open PRs block deploy unless you pass `--skip-pr-check`.

For multi-repo zip inventory and bulk ingest, use [`cli drive ingest`](drive.md).

**Debug tests:** `cli test python unit .` (fast host pytest) · `cli test python integration .` (tags + Docker unit + integration).

## Review (workspace health)

```bash
cli git review
```

Runs command-surface checks; without `--quick`, also `cli test python unit .`. No commit or push. Use `cli git review --quick` when full unit checks are unavailable.

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
