---
name: read-workflow-merge-conflicts
description: >-
  Read-only playbook: principles and steps to resolve git merge conflicts when merging into the current branch (local
  git only; no gh). Caller: @git-pull. Does not fetch, merge, or push.
visibility: internal
---
# Internal: Merge conflict resolution

**Read-only library.** **Local `git` only** (no **`gh`**). Use when **`@git-pull`** (or any parent) merges **`@{u}`** or **`ROOT_BRANCH`** and **`git`** leaves **unmerged paths**. **Ours** = current branch; **theirs** = the ref being merged (for example **`origin/main`** or a tracking branch).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Principles

- **Never blindly checkout sides** — Read conflict markers manually (`<<<<<<<`, `=======`, `>>>>>>>`), especially in manifests (`package.json`, `Cargo.toml`, `.gitignore`), where both sides' additions often need to be preserved together. Avoid `git checkout --theirs` / `--ours` across all files, which can silently wipe branch additions.
- **Accept what main/root brought** — For shared files and root-owned regions, default to **incoming (theirs)** unless a small local tweak is required for the branch to compile or meet its goal.
- **Avoid large rewrites of root code** — Do not replace big root blocks with older branch versions to “win” the merge. Keep root structure; adjust **branch additions** (new code, modules, tests) to fit.
- **Branch goal** — After merging, the feature or fix the branch exists for should still be achievable; adapt call sites, imports, and branch-only logic—not revert upstream refactors wholesale.

---

## Procedure (execute in order)

When any merge leaves unmerged paths:

1. **Confirm merge in progress** — `git status` shows unmerged paths.

2. **List conflicted files** — `git diff --name-only --diff-filter=U` (or `git status`).

3. **Resolve each conflict**
   - **Read the files first** to see the markers. **Never** blindly run `git checkout --theirs` or `git checkout --ours` across all files, especially for manifests (`package.json`, `.gitignore`, `Cargo.toml`).
   - **Default to incoming (theirs)** for overlapping regions in files **main/root** owns (shared modules, config patterns, APIs updated on root). Prefer their version, then fix **branch-only** breakages (imports, types, tests) in the smallest follow-up edits.
   - **Adapt branch code** — For files that are mostly **branch work**, keep branch intent but align with new root APIs and layout (move code, update signatures) rather than restoring pre-merge branch snapshots of root files.
   - **Remove conflict markers** and leave one coherent result. **Do not** mass-reformat or restyle root code to match the branch; keep root formatting when you kept their side.

4. **Stage** — `git add <file>` for each resolved file.

5. **Complete merge** — `git status` has no unmerged paths; `git commit` (default merge message unless the user specifies otherwise).

Then continue from the **parent** step that triggered the conflict (e.g. **`@git-pull`** §3 or §5).

---

## Do not (library)

- **Fetch**, **merge** (except completing the in-progress merge via **`git commit`** after resolution), or **`git push`** — parent skill owns merge invocations; **`@git-push`** owns publish.

---

## See also

- **[`@git-pull`](../../../git/pull/SKILL.md)** — source of truth for how `ROOT_BRANCH` is chosen before conflicts are resolved.
- **[`read-safety-skill-safety`](../../../internal/read/safety/skill-safety/SKILL.md)** — **`@git-pull`** merge-commit carve-out.
- **[`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md)** **§4** — ambiguous tree before merge.
