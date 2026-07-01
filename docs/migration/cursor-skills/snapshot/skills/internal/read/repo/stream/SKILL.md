---
name: read-repo-stream
description: >-
  Read-only library: classify fork vs same-repo, canonical main ref, PR target repo, BASE_GIT, and PR head/base for gh
  and git callers (no network I/O in this file). No fetch, merge, or gh pr create—callers run their own commands. Used by
  @git-main, @git-pull, @gh-pr, @git-reset.
---
# Internal: Git repo stream (fork vs same-repo)

**Read-only.** Discover **where canonical `main` lives** and **where a pull request is opened** (rules for **`git`** remotes/branches **and** **`gh --repo`** targets). Do **not** run `git fetch`, merges, `git reset`, or `gh pr create` here—parent skills own those steps.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- Classify fork vs same-repo and resolve **canonical main**, **PR targets**, and **`BASE_GIT`** for parent skills.

## Do not

- Run **`git fetch`**, merges, **`git reset`**, or **`gh pr create`**—parent skills own those steps.

---

## 1. Detect fork vs same-repo

1. Run **`shuttle git remote-url upstream`** (or equivalent).
2. **If success** — treat as **fork**:
   - **`UPSTREAM`** — `owner/repo` parsed from the URL (SSH or HTTPS).
   - **`FORK_OWNER`** — owner from **`shuttle git remote-url origin`** (the fork’s GitHub user or org).
   - **`STREAM_MODE`** = `fork`.
3. **If failure** — **same-repo** clone:
   - **`UPSTREAM`** — unset / empty (no upstream remote).
   - **`STREAM_MODE`** = `same_repo`.

**If the workflow is a fork but `upstream` is missing** — **stop**; suggest adding upstream remote and fetch via **`shuttle git`** / docs — do not guess **`UPSTREAM`**.

---

## 2. Canonical main ref (`CANONICAL_MAIN_REF`)

Single definition used by **`@git-main`** and **`@git-pull`** for “tip of mainline in this workspace”:

| Condition | `CANONICAL_MAIN_REF` |
| --- | --- |
| **`upstream` remote exists** | **`upstream/main`** |
| **Else** | **`origin/main`** |

Verify with **`shuttle git rev-parse "$CANONICAL_MAIN_REF"`** after remotes are fetched (callers fetch; this skill does not).

**Alias:** **`ROOT_BRANCH`** in **`@git-pull`** = **`CANONICAL_MAIN_REF`**. **`CANONICAL_MAIN`** in **`@git-main`** = same ref.

---

## 3. PR-oriented fields (for `@gh-pr` and `gh`)

Use **after** §1–§2 so **`STREAM_MODE`**, **`UPSTREAM`**, and **`FORK_OWNER`** are set.

| Variable | Fork (`STREAM_MODE=fork`) | Same-repo |
| --- | --- | --- |
| **`BASE_GIT`** | **`upstream/main`** | **`main`** or **`origin/main`**—match how **`@git-pull`** merged canonical **`main`** into the branch (typically **`main`** if checked out, else **`origin/main`**) |
| **`PR_TARGET_REPO`** | **`$UPSTREAM`** (`owner/repo` for `gh --repo`, `gh repo view`) | Current repo (**`gh repo view`** without `--repo` override) |
| **`PR_BASE_BRANCH`** | **`main`** on **`$UPSTREAM`** | **`main`** |

**GitHub PR base:** always **`main`** on the **destination** repo (**`$UPSTREAM`** for forks, else the current repo).

**Issue list / search / URLs:** For **`@gh-pr`** and **`read-pr-description`** §6.6, use **`PR_TARGET_REPO`** as **`--repo owner/repo`** and as **`https://github.com/OWNER/REPO/...`** host for issues and PRs on the **destination** (upstream when forking), unless the issue genuinely lives on the fork.

---

## 4. PR head ref (`--head` for `gh pr create`)

Let **`BRANCH`** = `shuttle git branch-current`.

| `STREAM_MODE` | `BRANCH` | PR **head** argument |
| --- | --- | --- |
| **same_repo** | `main` | *(no PR from this skill’s perspective—**`@gh-pr`** stops after sync)* |
| **same_repo** | feature | **`$BRANCH`** |
| **fork** | `main` | **`$FORK_OWNER:main`** — open PR **from fork’s `main`** to **`$UPSTREAM`** **`main`** |
| **fork** | feature | **`$FORK_OWNER:$BRANCH`** |

This is the **“proceed toward upstream”** case when you are on **fork `main`**: the PR targets **`$UPSTREAM`**, not the fork as base.

---

## 5. `gh` commands (reference—run in parent skill)

- **List / create / edit PR (fork):** pass **`--repo "$UPSTREAM"`** where **`@gh-pr`** already does.
- **Templates:** **`gh repo view --json`** shapes for **`pullRequestTemplates`** / **`issueTemplates`** live **only** in **[`read-repo-forms-json`](../repo-forms-json/SKILL.md)**—use the **fork** / **`$UPSTREAM`** rows there when **`PR_TARGET_REPO`** is upstream (not the fork as template host).

---

## 6. Relation to `@git-reset` target

When **`@git-reset`** resolves **`$TARGET`** and the branch is **`main`** with **`upstream/main`** available, prefer **`upstream/main`** as the canonical tip—consistent with **`CANONICAL_MAIN_REF`** above. **`@git-reset`** still uses tracking **`@{u}`** first when set; see that skill’s priority list.
