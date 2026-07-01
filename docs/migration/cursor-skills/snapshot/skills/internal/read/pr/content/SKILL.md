---
name: read-pr-content
description: >-
  Read-only: canonical PR title + body shape; child skills title-line/ and pr-body-skeleton/. Orchestration stays in
  read-pr-description + read-pr-body-sections. Callers: @gh-pr. Does not write files.
---
# Internal: PR content shape (`read-pr-content`)

**Read-only library.** **What** the **title** and **body** should look like. **Child skills:**

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Ownership

| Topic | Owner |
| --- | --- |
| Title line rules + body section order | **This skill** + **[`title-line/SKILL.md`](./title-line/SKILL.md)** + **`pr-body-sections/section-patterns`** |
| **`gh repo view --json`** (templates API) | **`read-repo-forms-json`** |
| Local template globs + merge / reshape | **`read-pr-description`** §5 |
| **`git log` / `git diff`** vs **`$BASE_GIT`** | **`read-diff-summary`** (§6 of **`read-pr-description`**) |
| API-first linking ladder + issue hint scan (read-only) | **`read-pr-description`** §6.5–6.6 |
| Title/body prose assembly + triple pass | **`read-pr-description`** §7 |
| Example markdown shape only | **[`pr-body-skeleton/SKILL.md`](./pr-body-skeleton/SKILL.md)** |

## See also

- [`read-diff-summary`](../../git/git-diff-summary/SKILL.md)
- [`@gh-pr`](../../../gh/pr/SKILL.md)
