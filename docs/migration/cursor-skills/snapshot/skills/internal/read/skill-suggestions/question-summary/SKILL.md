---
name: read-skill-suggestions-question-summary
description: >-
  Read-only: concise summary shape for suggested-next-step AskQuestion prompts after a public skill verifies.
  Keeps context short and decision-ready.
---
# Internal: suggestion question summary

Use this helper to format the **chat summary immediately before** the optional post-verify AskQuestion in **`## Recommended next steps`** (**`skip=false`** at root only).

**Not** the write-gate summary — pre-mutation gates use **[`read-safety-structured-qa-summary`](../../safety/structured-qa/summary/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Summary template

Keep the pre-question summary to 3-6 bullets:

1. **Current state** - what just completed (`CURRENT_SKILL`, verification result).
2. **Decision point** - what choice is needed now.
3. **Constraint** - risk, branch state, or scope caveat if relevant.
4. **Top path** - most likely next skill and why.
5. **Alternative path** - second/third option only when materially different.

### Post-review example (`@gh-pr-review`)

- **Current state:** PR #42 reviewed — verdict merge-ready.
- **Decision point:** Merge in GitHub UI, update PR, or file follow-up issues.
- **Top path:** merge in **GitHub UI**, then **`@gh-pr-view`** — confirm merged metadata.
- **Alternative:** **`@gh-issue-next`** — pick up the next backlog child.

## Do

- Keep the summary specific to this run (not generic boilerplate).
- Mention only facts needed to choose the next step.
- Align wording with the selected options from `read-skill-suggestions-next-steps-options`.

## Do not

- Re-explain the entire completed workflow.
- Include runnable command fences.
- Add more than one freeform outlet (handled by Q&A option shape).

## See also

- [`read-skill-suggestions`](../SKILL.md)
- [`read-skill-suggestions-next-steps-options`](../next-steps-options/SKILL.md)
- [`read-skill-suggestions-qa-alternative-options`](../qa-alternative-options/SKILL.md)
- [`read-safety-structured-qa`](../../safety/structured-qa/SKILL.md)
