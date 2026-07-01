---
name: read-pr-branch-context
description: >-
  Read-only: gather current branch, diff summary vs PR base, and publish readiness for @gh-pr branch
  confirmation gate. Uses local git for workspace state; no GitHub mutations.
---
# Internal: PR branch context (`read-pr-branch-context`)

**Read-only library.** Build the **branch placement summary** shown in chat before **`@gh-pr`** continues past preflight. Confirms the user is on the intended branch with the expected delta before draft or mutation.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## When

Run as the **first evidence step** inside **`read-pr-preflight-qa`** (before overlap / create-vs-edit questions) whenever **`@gh-pr`** is invoked for create or edit.

## Gather (run in order)

1. **`read-repo-stream`** — resolve **`PR_TARGET_REPO`**, **`PR_BASE_BRANCH`**, **`BASE_GIT`**, **`STREAM_MODE`**, head ref rules.
2. **Current branch** — `shuttle git branch-current` → **`HEAD_BRANCH`**.
3. **Diff vs base** — `shuttle git diff-stat --base "$BASE_GIT"`. Capture file count and top paths from output.
4. **Ahead / behind** — `shuttle git rev-list-count --base "$BASE_GIT"` when available.
5. **Publish readiness** — `shuttle git rev-parse HEAD` and `shuttle git publish-check --remote origin --branch "$HEAD_BRANCH"`.

## Chat summary (required)

Render a short block **above** the branch AskQuestion:

```text
Branch: <HEAD_BRANCH>
Target: <PR_BASE_BRANCH> on <PR_TARGET_REPO>
Diff: <N> files, +<ins> / -<del> vs <BASE_GIT>
Changed: <path1>, <path2>, … (truncate)
Publish: <pushed | N commit(s) not on origin>
```

**Same-repo on `main` with empty diff:** stop here — nothing to PR; do not open create path.

## AskQuestion shape

Per **[`read-safety-structured-qa`](../../../safety/structured-qa/SKILL.md)** §0:

- **Prompt** (one sentence): “Create or update a PR from this branch and diff?”
- **Options:** **Abort** (safe-first), **Wrong branch — stop**, **Proceed — correct branch**
- Put the summary block in **chat above** the modal, not inside option labels.

When the user picks **Wrong branch — stop**, end **`@gh-pr`** without mutation.

## Do not

- Run `shuttle gh pr create` / `shuttle gh pr edit`.
- Skip the summary when branch and diff are deducible.

## See also

- [`read-pr-preflight-qa`](../preflight-qa/SKILL.md)
- [`read-repo-stream`](../../repo/stream/SKILL.md)
- [`@gh-pr`](../../../../gh/pr/SKILL.md)
