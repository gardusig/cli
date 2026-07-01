---
name: read-skill-suggestions-qa-alternative-options
description: >-
  Read-only: option-shaping rules for suggested-next-step AskQuestion prompts.
  Defines safe defaults, alternatives, and done/not-now choices.
---
# Internal: suggestion Q&A alternatives

Use this helper to shape **post-verify** AskQuestion option labels after **`read-skill-suggestions-question-summary`** and **`read-skill-suggestions-next-steps-options`**.

**Not** write-gate options — pre-mutation gates use **[`read-safety-structured-qa-options`](../../safety/structured-qa/options/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Option shape

- Always include one **safe stop** option: `Done` or `Not now`.
- Offer up to **3 action options** mapped to concrete public skills.
- Keep labels short and outcome-based (verb + target).

## Recommended ordering

1. Best next action (highest confidence).
2. Secondary alternative.
3. Tertiary alternative (optional).
4. `Done` / `Not now`.

If risk is high or context is ambiguous, put `Not now` first.

## Label examples

- `Open or update PR (@gh-pr)`
- `Run verification gate (@git-review)`
- `Start implementation (@gh-issue-execute)`
- `Done for now`

## Do

- Ensure each option maps to one public `@...` skill (except Done/Not now).
- Keep options mutually clear (avoid near-duplicates).
- Match options to the pre-question summary and current state.

## Do not

- Present hidden mutations as neutral options.
- Offer more than 4 options unless user explicitly asks.
- Add freeform "Other..." when parent already offers chat outlet.

## See also

- [`read-skill-suggestions`](../SKILL.md)
- [`read-skill-suggestions-question-summary`](../question-summary/SKILL.md)
- [`read-skill-suggestions-next-steps-options`](../next-steps-options/SKILL.md)
- [`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md)
