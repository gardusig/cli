---
name: read-issue-preflight-qa
description: >-
  Read-only question bank for @gh-issue pre-flight. Helps gather goal, examples, counterexamples, and
  verification details before dedupe and mutation.
---
# Issue pre-flight Q&A

Use this before any issue create/edit mutation.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Gather (deducible first)

- Candidate title intent from user prompt and repository context.
- Existing related issue numbers/titles from list/search.
- Existing labels that might apply.
- Whether the user is carrying **multiple independent themes** (long multi-section paste or many unrelated bullets) — see **[`read-issue-dedupe` — Multi-intent clustering](../issue-dedupe/SKILL.md#multi-intent-clustering)**.

## Clarify (ask when ambiguous)

- Goal: what outcome should be true after completion?
- Examples: concrete "today vs desired" cases.
- Counterexamples: explicitly out-of-scope or invalid behavior.
- Constraints: compatibility, regressions to avoid, rollout risks.
- Verification: acceptance and regression checks.

## Iteration / ship gate (normative for `@gh-issue`)

After each refinement pass, once requirements and draft intent are summarized, **before** list/dedupe, the caller must offer a single structured choice (AskQuestion per [`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md), safe-first when ordering matters):

- **Abort** — stop or park; do not run inventory/dedupe for publish.
- **Sharpen** — another Q&A round in chat; then re-summarize and ask again.
- **Ship** — candidate is good enough to continue the pipeline (list → dedupe → description → mutation confirm).

Repeat until **Ship** or **Abort**. Optional readiness hints: outcome, scope, non-goals, acceptance + regression verification, and risks/unknowns are explicit enough to execute.

## Multi-topic paste

When a **long multi-topic** paste is present, optionally use structured AskQuestion (same § as the ship gate) to confirm **one combined issue** vs **multiple themes** after **Ship** (then **`read-issue-dedupe`** **Multi-intent clustering**). Default remains one narrative until the user opts into multi-intent.

## AskQuestion shape

Per **[`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md) §0 / §1f** via **[`read-safety-structured-qa-question`](../../safety/structured-qa/question/SKILL.md)** + **[`read-safety-structured-qa-options`](../../safety/structured-qa/options/SKILL.md)**:

- Put draft intent, dedupe hints, and **#n — title** rows in the **assistant summary above** AskQuestion—not in the modal prompt.
- Keep the **prompt** to one short English sentence (for example, “Ready to ship this issue draft?”).
- Keep options safe-first (**Abort** / **Sharpen** / **Ship**); no issue body text in labels.
- Use one refinement outlet only.

## See also

- [`read-issue-spec`](../spec/SKILL.md)
- [`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md)
- [`read-issue-dedupe`](../issue-dedupe/SKILL.md)
- [`@gh-issue`](../../../gh/issue/SKILL.md)
