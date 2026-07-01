# Common usage flows

Visual maps for everyday `cli` workflows. Command details live in [git.md](git.md) and [quick-defaults.md](quick-defaults.md).

## Full issue lifecycle

```mermaid
flowchart TD
    subgraph before [1 — Before work]
        P["cli git reset --yes --main-only<br/>sync main"]
    end

    subgraph start [2 — Start issue]
        K["cli git start issue-9-slug --yes<br/>align main + new branch"]
    end

    subgraph loop [3 — During work]
        D["edit files"]
        S["cli git push<br/>add · commit · push"]
        Y["cli git pull<br/>stay current on main"]
        D --> S
        S --> D
        Y --> D
    end

    subgraph after [4 — After merge]
        L["cli git reset --yes<br/>sync main · optional merged branch cleanup"]
        L2["cli git reset --yes --all-local<br/>delete every local branch except main"]
    end

    P --> K --> loop
    loop --> PR["gh pr create · merge"]
    PR --> L
    L --> P
```

| Phase | Shortcut | What it does | Older equivalent |
| --- | --- | --- | --- |
| Sync main | `git reset --yes --main-only` | checkout `main`, fetch, pull/ff or hard-reset, clean worktree | `git main --yes` |
| Start issue | `git start [branch] --yes` | align main + `checkout -b` | — |
| Publish WIP | `git push --yes` | add + commit + push current branch; on `main`, start random branch first | `git commit` + `git push` |
| Stay current | `git pull` | fetch + merge upstream/main into feature branch | — |
| After merge | `git reset --yes --delete-merged` | return to synced main + delete **merged** branches | `git post merge cleanup --yes` |
| Nuclear local | `git reset --yes --all-local` | synced main + delete **all** local branches except main | `git branch clear --yes` |

All destructive steps show the **write gate** (branch, dirty state, intent) before running. Pass `--yes` / `-y` to skip the prompt (summary still prints).

**Leaving a feature branch:** `reset` commits uncommitted work on the current branch (message `.` by default) before syncing `main`. Pass `--discard` to drop uncommitted changes instead.

### Example session

```bash
# Monday: synced main
cli git reset --yes --main-only

# Pick up GitHub issue #9
cli git start issue-9-docker --yes

# Loop until PR is ready
cli git push          # interactive
cli git pull          # optional: merge latest main
cli git push --yes

# After PR merged
cli git reset --yes
# answer the follow-up prompt to run `branch delete --merged`, or:
cli git reset --yes --delete-merged
```

## GitHub phase (after PR is open)

One CLI command and one script per step. See [gh.md](gh.md) and [scripts/gh/README.md](../scripts/gh/README.md).

| Step | CLI | Script |
| --- | --- | --- |
| Pick next issue | `gh backlog next` | `./scripts/gh/backlog-next.sh` |
| View issue | `gh issue view N` | `./scripts/gh/issue-view.sh N` |
| Open PR | `gh pr create … --yes` | `./scripts/gh/pr-create.sh … --yes` |
| Check PR | `gh pr view N` | `./scripts/gh/pr-view.sh N` |
| **Merge PR** | **GitHub UI / auto-merge** | *(not `cli gh pr merge` — blocked)* |
| Close issue | `gh issue close N --yes` | `./scripts/gh/issue-close.sh N --yes` |

**Full chain:** `backlog next → reset → start → push → review → pr create → [UI merge] → issue close → reset`

### Example (GitHub steps)

```bash
./scripts/gh/backlog-next.sh --format json
# … git work on branch …
./scripts/git/review.sh
./scripts/gh/pr-create.sh --title "." --body "" --yes
# merge in GitHub UI (or enable auto-merge on the PR)
./scripts/gh/issue-close.sh 42 --comment "Done" --yes
./scripts/git/reset.sh --yes --delete-merged
```

GitHub Projects and Rulesets are **not** used from `cli` — use `cli gh backlog organize` and `priority:N` labels instead ([#72](https://github.com/gardusig/cli/issues/72) deferred).

## Feature work (start → publish)

```mermaid
flowchart LR
    subgraph setup [Setup once]
        A["./scripts/pypi/install.sh"]
    end

    subgraph daily [Daily loop]
        C["cli git start --no-prep"]
        D["edit files"]
        E["cli git push"]
        F{"more work?"}
        G["open PR / merge"]
        C --> D --> E --> F
        F -->|yes| D
        F -->|no| G
    end

    A --> C
```

## Sync with main (on feature branch)

```mermaid
flowchart TD
    A["on feature branch"] --> B["cli git pull<br/>fetch + merge upstream + main"]
    B --> C{conflicts?}
    C -->|no| D["cli git push"]
    C -->|yes| E["resolve conflicts"]
    E --> D
```

## Write gate (destructive / remote)

```mermaid
flowchart TD
    A["push / reset / start …"] --> B["read worktree snapshot"]
    B --> C["intent summary<br/>branch · dirty · plan"]
    C --> D["--- cli write gate ---"]
    D --> E{"--yes or confirm?"}
    E -->|no| F["Aborted"]
    E -->|yes| G["run git steps"]
```

## After merge (cleanup options)

```mermaid
flowchart TD
    A["PR merged on GitHub"] --> B{"how aggressive?"}
    B -->|default| C["cli git reset --yes --delete-merged<br/>merged branches only"]
    B -->|nuclear local| D["cli git reset --yes --all-local"]
    B -->|legacy| E["cli git post merge cleanup --yes"]
    B -->|remote too| F["cli git branch clear --yes --delete-remote"]
```

## Health check & bookmarks

```mermaid
flowchart LR
    subgraph review [Workspace health]
        R1["cli git review"]
        R2["shell syntax · test/unit.sh in Docker"]
        R1 --> R2
    end

    subgraph bookmarks [Chrome bookmarks]
        B1["./scripts/chrome/export.sh"]
        B2["configured bookmarks.html"]
        B3["./scripts/chrome/import.sh"]
        B1 --> B2 --> B3
    end

    subgraph docker [Isolated checks]
        D1["./scripts/test/integration.sh"]
        D2["copy repo · pytest · smoke · live docker"]
        D1 --> D2
    end
```

## Integration workflow tests

Four Docker E2E workflows (fixture config only — never host `~/git-local` or live `config/config.yaml`):

| Workflow | Steps |
| --- | --- |
| Plan → issues | `gh issue batch` → `backlog tree` → `backlog next` |
| Issue context | `gh issue context N` — epic, siblings, comments, linked issues |
| Dirty branch → PR | `git push --yes` → `gh pr create --yes` |
| Reset to main | nested dirty branches → `git reset --yes --delete-merged` |

Run on host (mocked `gh`): `./scripts/test/workflows.sh`  
Docker gate: `tests/integration/check_workflows.py` (wired in `scripts/test/smoke.sh`)

Config isolation: default `CLI_CONFIG_DIR=config/ci`; per-workflow overrides under `tests/fixtures/workflows/<name>/config.yaml`.

## Discover commands

```mermaid
flowchart TD
    A["cli --help"] --> B["cli links<br/>full index"]
    B --> C["docs/README.md"]
    B --> D["scripts/git/*.sh · scripts/gh/*.sh"]
    A --> F["cli git --help"]
```

See also: [Architecture](architecture.md) · [Docker integration](docker.md) · `cli links`

## Merge policy {#merge-policy}

**Never merge from `cli`.** Use the GitHub UI or enable **auto-merge** on the PR after green checks.

- `cli gh pr merge` exits non-zero with a policy message
- `scripts/gh/pr-merge.sh` is a warning stub (exit 1)
- Raw `gh pr merge` is blocked in `GhProvider` unless `CLI_ALLOW_GH_MERGE=1` (break-glass only)

Workflow chain ends at `[UI merge]` — not `cli gh pr merge`.
