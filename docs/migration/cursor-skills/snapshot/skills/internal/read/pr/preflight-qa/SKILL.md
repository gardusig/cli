---
name: read-pr-preflight-qa
description: >-
  Read-only question bank for @gh-pr pre-flight. Ensures source/target branch intent, readiness, and
  overlap handling are clarified before create/edit mutations.
---
# PR pre-flight Q&A

Use this before PR create/edit mutation.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Gather (deducible first)

1. **[`read-pr-branch-context`](../branch-context/SKILL.md)** — current branch, diff stat vs base, publish readiness; **write gate** **branch_placement** before other preflight questions.
2. Source branch (`HEAD`) and target base branch (from branch-context + **`read-repo-stream`**).
3. Existing matching PRs by head/base/title.
4. Repo stream context (same-repo vs fork).

## Branch placement gate (required)

After **`read-pr-branch-context`** summary in chat, **AskQuestion** per that library. **Stop** on **Abort** or **Wrong branch — stop**.

## Clarify (ask when ambiguous)

- Should this update an existing PR or open a new PR?
- If existing PR matches, which PR number should be edited?
- Is branch state ready to ship (green checks expected)?
- Any explicit reason to keep draft/WIP instead of ready-for-review?

## AskQuestion shape

Per **[`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md) §0 / §1f** via **[`read-safety-structured-qa-question`](../../safety/structured-qa/question/SKILL.md)** + **[`read-safety-structured-qa-options`](../../safety/structured-qa/options/SKILL.md)**:

- Put match evidence (head/base, **#n — title** table) in the **assistant summary above** AskQuestion—not in the modal prompt.
- Keep the **prompt** to one short English sentence (for example, “Update an existing PR or create a new one?”).
- Option labels: **Abort** (safe-first), then **#n — title** per matching PR or **Proceed — create new**; no PR body text.
- Use one refinement outlet only.

## See also

- [`read-pr-list`](../pr-list/SKILL.md)
- [`read-pr-description`](../pr-description/SKILL.md)
- [`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md)
- [`@gh-pr`](../../../../gh/pr/SKILL.md)
