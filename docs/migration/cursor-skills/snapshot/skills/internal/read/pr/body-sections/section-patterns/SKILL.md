---
name: read-pr-body-sections-section-patterns
description: >-
  Read-only: canonical PR body sections and examples. Parent read-pr-body-sections. No default Linked issues
  prose; optional minimal closing-keyword line only when @gh-pr §9 chose the keyword path.
---
# Canonical internal scaffold

This file is the canonical internal reference for PR section patterns.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Issue and project linkage (with `@gh-pr`)

- **Do not** add a standing **“Linked issues”** markdown section by default. Candidate issues and the **linking** (minimal **`Refs`/`Fixes`/`Closes`** line, or **UI-only**) are confirmed in **`@gh-pr`** **§9** per **[`read-pr-description`](../../pr-description/SKILL.md)** §6.5–7.
- **Minimal keyword line:** GitHub’s documented programmatic path for merge-time **closing** inference is **closing keywords in the PR body** (see **`read-shuttle-gh-pr-commands`**). At most **one** short trailing line when the user explicitly chose that path—**no** multi-paragraph issue prose in the PR description for traceability alone.
