---
name: read-skill-suggestions
description: >-
  Read-only: suggestive follow-up guidance for public @gh-* skills after Verification.
  Routes callers to nested suggestion helpers for question summary, options, and next-step catalog.
---
# Internal: skill suggestions (`read-skill-suggestions`)

**Read-only library.** Keep this as a lightweight router for "what to suggest next" after a public skill completes **Verification**. **Not** a substitute for pre-write **write gate** (**[`read-safety-structured-qa`](../safety/structured-qa/SKILL.md) §0**).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Suggestions-only contract

- This library provides **suggestions only**.
- It does not redefine public-skill orchestration order.
- It does not include runnable `git` / `gh` fences.
- It does not auto-run next skills.
- It is **root-aware**: prompt only when `skip=false` (root user-invoked public skill); suppress optional prompting when `skip=true` (nested child public-skill call).

## How to use (callers)

1. Resolve **`CURRENT_SKILL`** = public skill `name:` (for example `gh-pr-review`).
2. Resolve **`skip`** per **[`read-safety-structured-qa`](../safety/structured-qa/SKILL.md) §9a**:
   - Root user invocation: **`skip=false`** → continue to step 3 when **Verification** passed.
   - Nested public-skill child call: **`skip=true`** → **stop** (no next-step AskQuestion).
3. If **`SKIP_SUGGESTIONS=true`** (ENV) → **stop** even at root.
4. Build pre-question context via **[`read-skill-suggestions-question-summary`](./question-summary/SKILL.md)**.
5. Pick candidates from **[`read-skill-suggestions-next-steps-options`](./next-steps-options/SKILL.md)**.
6. Shape labels via **[`read-skill-suggestions-qa-alternative-options`](./qa-alternative-options/SKILL.md)**.
7. Offer **one** optional AskQuestion with top **1–3** applicable options + **Done** / **Not now**.
8. Skip when user already named the next skill, declined further work, or **`SKIP_QA_*`** blocked the parent workflow entirely.

## Post-merge chain (post-verify Q&A)

After a **root** public skill passes **Verification**, offer **one** AskQuestion — do not auto-run the next skill. When the user just merged a PR, prefer **`@gh-pr-view`** (confirm merged state) then **`@gh-issue-next`** or **Done** per **[`read-skill-suggestions-next-steps-options`](./next-steps-options/SKILL.md)**.

Every public **`@gh-*`** skill with **`## Recommended next steps`** should have a matching **`### \`name\``** section in the next-steps catalog (fallback: **`Done`** only).

## See also

- [`read-skill-suggestions-question-summary`](./question-summary/SKILL.md)
- [`read-skill-suggestions-qa-alternative-options`](./qa-alternative-options/SKILL.md)
- [`read-skill-suggestions-next-steps-options`](./next-steps-options/SKILL.md)
- [`read-safety-structured-qa`](../safety/structured-qa/SKILL.md) — **§9** AskQuestion contract
- [`docs/onboarding.md`](../../../docs/onboarding.md) — human onboarding
