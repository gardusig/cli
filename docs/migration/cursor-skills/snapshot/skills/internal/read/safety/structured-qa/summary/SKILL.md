---
name: read-safety-structured-qa-summary
description: >-
  Read-only: craft the chat summary above a write-gate AskQuestion (goal, facts, #n — title rows). Runs before
  read-safety-structured-qa-question and read-safety-structured-qa-options. Not for public @git-* / @gh-* skills.
---
# Internal: write-gate summary (`read-safety-structured-qa-summary`)

**Read-only library.** Shape the **assistant message immediately above** AskQuestion for pre-write gates. **Callers** run this as **step 1** of **write gate** in **[`read-safety-structured-qa`](../SKILL.md)** — before **[`read-safety-structured-qa-question`](../question/SKILL.md)** and **[`read-safety-structured-qa-options`](../options/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../language-interaction-rules/SKILL.md) first. English only unless the user explicitly requested another full-language response.

## Input (caller supplies)

- **Gate kind** — from **[`read-safety-structured-qa-question`](../question/SKILL.md)** catalog.
- **Facts** — branch names, diff stat, file counts, repo, refs, candidate **#n — title** rows, commit message draft, mutation list.
- **Goal** — one-line outcome if the user confirms.

## Output shape

Keep to **3–8 bullets** or one compact table:

1. **Goal** — one line (“Publish branch `feature/x` to `origin`”).
2. **Targets** — branch, tag, PR/issue **#n — title**, remote, base ref.
3. **Impact** — file count, delete count, force/collision risks when relevant.
4. **On Proceed** — which **`write-*`** blocks or next skill step run.

**PR/issue rows:** **`#n — title`** only; link **#n** when URL is known. **No** bodies or long descriptions.

## Do

- Put **all detail here** — the AskQuestion prompt and options stay minimal.
- Use tables for multiple PR/issue/branch candidates.
- Call out non-default paths (for example **Proceed on `main`**) explicitly.

## Do not

- Paste content that belongs in the modal prompt or option labels.
- Exceed what the user needs to choose safely (~15 lines max).

## See also

- [`read-safety-structured-qa`](../SKILL.md) — **§0** write gate
- [`read-safety-structured-qa-question`](../question/SKILL.md)
- [`read-safety-structured-qa-options`](../options/SKILL.md)
