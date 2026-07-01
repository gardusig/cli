---
name: read-safety-structured-qa-question
description: >-
  Read-only: craft one short English AskQuestion prompt for pre-write gates. Summary lives in chat above the modal;
  this library shapes the prompt only. Caller: read-safety-structured-qa write gate. Not for public @git-* / @gh-* skills.
---
# Internal: write-gate question (`read-safety-structured-qa-question`)

**Read-only library.** Shape **one short AskQuestion prompt** immediately before a write mutation. **Callers** run this as step 2 of the **write gate** in **[`read-safety-structured-qa`](../SKILL.md)** — after **[`read-safety-structured-qa-summary`](../summary/SKILL.md)**, before **[`read-safety-structured-qa-options`](../options/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../language-interaction-rules/SKILL.md) first. English only for prompt text unless the user explicitly requested another full-language response.

## Input (caller supplies)

- **Gate kind** — see catalog below.
- **Summary already posted** — goal, targets, counts, **#n — title** rows, diff stat, branch names (all detail stays in chat, not in the prompt).
- **User intent** — what decision this gate resolves.

## Output

- **One English sentence** for the AskQuestion **`prompt`** field.
- **≤ ~120 characters** when practical; identifiers only if needed for disambiguation.
- **No** PR/issue bodies, diffs, tables, or bullet lists inside the prompt string.

## Gate kind catalog

| Kind | When | Prompt pattern (examples) |
| --- | --- | --- |
| **binary_proceed** | Single yes/no before one mutation | “Proceed with commit and push?” · “Proceed with this reset?” |
| **triage** | §1e Abort / Review / Proceed | “Proceed with these GitHub writes?” · “Continue with bulk delete?” |
| **ship** | `@gh-issue` pre-dedupe | “Ready to ship this issue draft?” · “Continue to dedupe and publish?” |
| **disambiguate_pr** | Matching open PRs | “Which PR should be updated?” · “Update an existing PR or create a new one?” |
| **disambiguate_issue** | Pick among issues | “Which issue should we tackle next?” · “Edit an existing issue or create new?” |
| **staging** | Commit scope / message | “Proceed with this commit?” · “Which staging scope should be used?” |
| **failure** | §8 publish/mutation failure | “Push failed on `branch`; choose next step.” |

Pick the **smallest** kind that resolves the decision. Do not combine unrelated decisions in one prompt.

## Do

- State the **decision** only — action verb + object.
- Assume the user read the summary above the modal.
- Match gate kind to **[`read-safety-skill-safety`](../../skill-safety/SKILL.md)** trigger row when applicable.

## Do not

- Repeat facts from the summary (branch lists, file counts, PR bodies).
- Use non-English prompt text without explicit user request.
- Ask multiple questions in one prompt string.
- Embed markdown links or tables in the prompt.

## See also

- [`read-safety-structured-qa-summary`](../summary/SKILL.md) — chat summary before this step
- [`read-safety-structured-qa`](../SKILL.md) — write gate orchestration
- [`read-safety-structured-qa-options`](../options/SKILL.md) — option labels for the same gate
- [`read-safety-language-interaction-rules`](../../language-interaction-rules/SKILL.md)
