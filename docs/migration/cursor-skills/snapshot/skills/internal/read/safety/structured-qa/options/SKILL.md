---
name: read-safety-structured-qa-options
description: >-
  Read-only: craft safe-first AskQuestion option labels after the prompt is chosen. Detail stays in chat summary;
  labels stay short. Caller: read-safety-structured-qa write gate. Not for public @git-* / @gh-* skills.
---
# Internal: write-gate options (`read-safety-structured-qa-options`)

**Read-only library.** Shape **finite AskQuestion option labels** for pre-write gates. **Callers** run this as step 3 of the **write gate** in **[`read-safety-structured-qa`](../SKILL.md)** — after **[`read-safety-structured-qa-summary`](../summary/SKILL.md)** and **[`read-safety-structured-qa-question`](../question/SKILL.md)** — before invoking AskQuestion.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../language-interaction-rules/SKILL.md) first. English only for option labels unless the user explicitly requested another full-language response.

## Input (caller supplies)

- **Gate kind** — same catalog as **[`read-safety-structured-qa-question`](../question/SKILL.md)**.
- **Summary already posted** — identifiers and titles live here, not in labels when duplicated.
- **Chosen prompt** — from the question library (do not re-derive).

## Output

- **2–12** option labels, **safe-first** when order matters.
- Each label **≤ ~80 characters**; truncate long titles with `…`.
- Map each label to **exactly one** downstream action on **Proceed**.

## Option patterns by gate kind

| Kind | Safe-first order | Label examples |
| --- | --- | --- |
| **binary_proceed** | negative first | `No` · `Yes` — or `Abort` · `Proceed` |
| **triage** | stop first | `Abort` · `Review` · `Proceed` |
| **ship** | stop first | `Abort` · `Sharpen` · `Ship` |
| **disambiguate_pr** | stop first | `Abort` · `#42 — short title` · `Create new PR` |
| **disambiguate_issue** | stop first | `Cancel` · `#17 — short title` · `Create new issue` |
| **staging** | abort first | `Abort` · `Proceed — full tree` · `Tracked only` · `Selected paths` |
| **failure** | stop first | `Abort` · `Change approach` · `Retry push` |

### PR and issue rows (§1f)

- Options show **`#n — title`** only — never body text.
- Prefer **`Proceed — edit #n`** when the action is explicit.
- For many matches, offer top **N** (≤ 8) plus **`Create new`** / **`Refine`** — narrow in chat per **§4** if needed.

### Multi-action batch (`@gh-issue`)

- **`Proceed — batch`** when one confirm covers ordered creates/edits already listed in the summary table.
- Optional **`Defer selected themes`** when the parent skill allows partial execution.

## Do

- Use **verb + object** or **`#n — title`** — never paragraphs.
- Keep options **mutually exclusive** unless `allow_multiple: true` is explicitly required (rare).
- Offer **one** freeform outlet per **[`read-safety-structured-qa`](../SKILL.md) §5** — not duplicate “Other…” paths.

## Do not

- Paste PR/issue bodies, diffs, or markdown blocks into option text.
- Hide risky actions behind generic **Proceed** — name force/push/reset risk in the label when applicable.
- Use non-English labels without explicit user request.
- Exceed **12** options — narrow first.

## See also

- [`read-safety-structured-qa`](../SKILL.md) — write gate orchestration · **§1f** · **§2** · **§5**
- [`read-safety-structured-qa-summary`](../summary/SKILL.md)
- [`read-safety-structured-qa-question`](../question/SKILL.md)
- [`read-safety-language-interaction-rules`](../../language-interaction-rules/SKILL.md)
