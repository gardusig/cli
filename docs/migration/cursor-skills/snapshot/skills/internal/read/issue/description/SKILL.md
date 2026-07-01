---
name: read-issue-description
description: >-
  Read-only: discover GitHub/local issue templates vs pack body skeleton; when merge would materially reshape
  repo template, structured AskQuestion (keep / blend / pack). Caller: gh-issue. Does not run gh.
---
# Internal: Issue description (templates vs pack)

**Read-only library.** Run **after** **[`read-issue-dedupe`](../issue-dedupe/SKILL.md)** when the user wants a **tracked** issue, **before** drafting final **title/body** for the chosen create-or-edit path in **`@gh-issue`**. **Pack pasteable:** **[`issue-body-skeleton/SKILL.md`](./issue-body-skeleton/SKILL.md)**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## 1. Discover issue templates

### Step A — `gh repo view` (required when `gh` works)

The **caller** executes the **`gh repo view … --json issueTemplates`** line(s) from **[`read-repo-forms-json`](../repo-forms-json/SKILL.md)** § **Issue templates** (default row unless the caller already chose the **upstream** row for fork parity). **Do not** duplicate those commands here.

**Parse** **`issueTemplates`** (field may be **absent** on older **`gh`** builds—treat as empty and continue to **Step B**).

- **One or more YAML/form** templates (`.github/ISSUE_TEMPLATE/**`) may appear as **names** only—if **no** usable **markdown body**, continue to **Step B**.
- If **API returns usable markdown** for **exactly one** template → set **`$ISSUE_TEMPLATE_SOURCE`** = `github-api`, **`$ISSUE_TEMPLATE_BODY`** = that body.
- **Two or more** usable markdown bodies → **template selection Q&A** per **[`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md)** (one option per template + **“Pack skeleton only”** → empty body, pack shape only).
- **Empty / missing** → **Step B**.

### Step B — Local files (when Step A yields nothing usable)

Search the **current** clone:

- **`.github/ISSUE_TEMPLATE.md`**, **`.github/issue_template.md`**
- **`.github/ISSUE_TEMPLATE/*.md`** (ignore **`config.yml`** for body text)
- **`docs/issue_template.md`** (optional convention)

Use **`git ls-files`** + glob.

- **Exactly one** **`.md`** → **`$ISSUE_TEMPLATE_SOURCE`** = `local`; **`$ISSUE_TEMPLATE_BODY`** = contents.
- **Two or more** → **template selection Q&A** (same as PR **multiple templates** pattern).
- **None** → **`$ISSUE_TEMPLATE_SOURCE`** = `canonical`; **`$ISSUE_TEMPLATE_BODY`** = **empty**.

### Step C — Pack only

**`$ISSUE_TEMPLATE_SOURCE`** = **`canonical`**; **`$ISSUE_TEMPLATE_BODY`** = **empty**. Draft body from **[`issue-body-skeleton/SKILL.md`](./issue-body-skeleton/SKILL.md)** and quality-check against **[`read-issue-spec`](../issue-spec/SKILL.md)**.

---

## 2. Material reshape vs pack skeleton

When **`$ISSUE_TEMPLATE_BODY`** is **non-empty**, compare its **headings / required sections** to the pack **`body-skeleton`**. If applying the pack skeleton would **replace** the repo template’s top-level structure (e.g. force **Context / Proposal** where the template uses **Bug report** sections), treat as **material**.

**Before** merging shapes, the **caller** runs **AskQuestion** (short labels), **separate** from the final **`gh issue create`** / **`gh issue edit`** confirm:

1. **Keep repo template** — substance only inside existing sections.
2. **Blend** — keep repo headings; add **non-duplicative** pack sections the template omits (minimal).
3. **Pack skeleton** — draft from **`body-skeleton.md`**; ignore repo template **shape** (keep links/checklists from repo only if user asks in chat).

Set **`$ISSUE_BODY_SHAPE_MODE`** to **`keep`** | **`blend`** | **`pack`** for the caller.

When **`$ISSUE_TEMPLATE_SOURCE`** is **`canonical`**, set **`$ISSUE_BODY_SHAPE_MODE`** = **`pack`** with **no** extra modal.

---

## 3. Hand off

Return to **`@gh-issue`**: draft **title** per **[`TITLE_LINE.md`](../pr-content/TITLE_LINE.md)**; draft **body** using **`$ISSUE_TEMPLATE_BODY`**, **`$ISSUE_TEMPLATE_SOURCE`**, and **`$ISSUE_BODY_SHAPE_MODE`**; then run **Goal** + **Proceed** before `gh`.

## See also

- **[`read-repo-forms-json`](../repo-forms-json/SKILL.md)** — **`gh repo view --json`** shapes for templates.
- **[`read-pr-description`](../pr-description/SKILL.md)** — PR-side discovery + merge rules (mirror concepts).
- **[`read-issue-dedupe`](../issue-dedupe/SKILL.md)** — duplicate search before writes.
- **[`read-issue-labels`](../issue-labels/SKILL.md)** — optional label proposals after title/body exist.
