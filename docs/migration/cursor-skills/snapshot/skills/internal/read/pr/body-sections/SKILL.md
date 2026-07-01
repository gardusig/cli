---
name: read-pr-body-sections
description: >-
  Read-only: PR title/body markdown patterns and canonical section structure. Caller: read-pr-description.
  Does not run gh or git.
---
# Internal: Pull request body sections (`read-pr-body-sections`)

**Read-only library.** **Static** PR **substance**: section headings, canonical body rules, example skeleton, title rules. Full copy-paste reference: **[`section-patterns/SKILL.md`](./section-patterns/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- When **`$PR_TEMPLATE_SOURCE`** is **`canonical`**, draft the body from **`section-patterns/SKILL.md`** only.
- When merging a repo or GitHub template, **map** content into those headings while keeping **TL;DR** first.

## Do not

- Run **`gh pr create`**, **`gh pr edit`**, or **AskQuestion** for PR mutation — parent **`@gh-pr`** §9.

---

## See also

- [`read-pr-content`](../pr-content/SKILL.md) — title/body shape (**`title-line`**, **`pr-body-skeleton`**)
- [`read-pr-description`](../pr-description/SKILL.md) — discovery, §6 delta, §6.5–7 linking + title/body
- [`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md) — template pick when multiple templates
- [`@gh-pr`](../../../gh/pr/SKILL.md)
