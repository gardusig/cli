---
name: read-pr-description
description: >-
  Read-only: PR template discovery (§5), delta (§6), API-first issue/linking ladder + issue hint scan (§6.5–6.6), title/body + triple-pass (§7).
  Caller @gh-pr after §5; parent §9 mutates. Does not run gh pr create/edit.
---
# Internal: PR description

**Read-only.** Run after **`@gh-pr`** **§5** (**`PR_NUM`**, **`$BASE_GIT`**, branch/upstream vars per **`read-repo-stream`**). When open PR matches existed in §5, treat **`PR_NUM`** as user-confirmed intent from that AskQuestion gate. **Does not** mutate GitHub or own **Proceed** for PR apply—that is **`@gh-pr`** **§9** (**`read-safety-skill-safety`** + **`read-safety-structured-qa`** **§3a**).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## 5. Discover PR templates

Run **after §4**, **before §6**. **Step A** always first (**`gh`** JSON); **B** if no usable template; **C** if still none.

**Multiple templates:** structured pick per **`read-safety-structured-qa`** (one option per template + **Canonical only** → **`$PR_TEMPLATE_SOURCE`** = **`canonical`**, empty body).

### Step A — GitHub API (required)

**Execute** (do not copy-paste from here): same-repo vs fork command from **`read-repo-forms-json`** § **Pull request templates** using **`PR_TARGET_REPO`** / **`$UPSTREAM`** from **`read-repo-stream`** §3.

- Parse **`pullRequestTemplates`** (length probe in repo-forms-json optional; read full entries when non-empty).
- **One** object → **`github-api`** + body markdown.
- **≥2** → template Q&A.
- **`[]` / missing** → Step B. **`gh`** error after retry → B + note.

### Step B — Local files

Globs and filenames: **`read-pr-body-sections`** (do not maintain a second list here). Discover with **`git ls-files`** + glob. **One** file → **`local`**; **≥2** → Q&A; **none** → Step C.

### Step C — Canonical

**`$PR_TEMPLATE_SOURCE`** = **`canonical`**, **`$PR_TEMPLATE_BODY`** empty — scaffold from **[Body — canonical structure](#body--canonical-structure)** via **`read-pr-body-sections/section-patterns/SKILL.md`**.

### Merge rules (all sources)

**Non-canonical body:** template owns headings/checklists; canonical rules govern **substance** (prepend **TL;DR** / **What changed** when template has no short opener—unless template forbids; strip checklist items that only duplicate **Files changed**).

**Material template reshape:** **`read-safety-structured-qa`** **AskQuestion** — **Keep / Blend / Pack canonical** — when applying the rules above would **reorder/remove** template-defined headings (**separate** from **`@gh-pr`** §9 PR mutation).

---

## 6. PR delta

Run **`read-diff-summary`** **in full**. **§7** “What changed” must track that output—no parallel **`git`** recipes here.

---

## 6.5 Linking (read-only orientation)

Use this when deciding what to put in the **§9** mutation summary (and therefore what **`@gh-pr`** may run after **Proceed**). **Do not** imply undocumented GitHub APIs for the PR **Development** sidebar link.

1. **Keyword path** — **`Refs #n` / `Fixes #n` / `Closes #n`** in the PR body (or body file) per **[`read-shuttle-gh-pr-commands`](../../shuttle/gh/pr-commands/SKILL.md)**. There are **no** separate `gh pr create` flags for Development linkage.

2. **UI-only path** — Omit keywords; user links issues in the GitHub UI. Platform gap for programmatic Development picker: [`cli/cli#11405`](https://github.com/cli/cli/issues/11405). See [Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue).

3. **Read-only verification** — After create/edit, parents may run **`shuttle gh pr view`** with JSON including **`closingIssuesReferences`** (see **`read-shuttle-gh-pr-read`**) to confirm what GitHub inferred—**read** only.

---

## 6.6 Issue hint scan (read-only)

Collect **candidate issue numbers** and evidence for **`@gh-pr`** **§9** (optional minimal keyword line or UI-only). **Do not** add a default **“Linked issues”** prose block to the PR body from this scan alone.

**Evidence order (strongest first):**

1. Explicit **`#nnn`** or **`Fixes` / `Refs` / `Closes`** in user chat or pasted intent.
2. **Branch name** tokens (for example `issue-42`, `fix/123-short-title`, `…-#42-…`). Prefer explicit **`#`** patterns over naive long digit runs from paths.
3. **Commit messages** on **`$BASE_GIT..HEAD`** — use full bodies, not only **`git log -1`**, so branch-wide **`Fixes #n`** / **`Refs #n`** surface; recipes in **[`read-diff-summary/delta-narrative`](../../git/git-diff-summary/delta-narrative/SKILL.md)** (**Issue keywords in commit range**).
4. **Optional validation** on **`PR_TARGET_REPO`** (same **`owner/repo`** as the PR destination—**forks:** use **`$UPSTREAM`**, not the fork root). Shapes: **[`read-shuttle-gh-issue-read`](../../shuttle/gh/issue-read/SKILL.md)** (`shuttle gh issue list`, `shuttle gh issue search` with **`--repo`** as needed).

**Heuristics:** If candidates disagree, defer to **`@gh-pr`** **§9** **AskQuestion**—do not auto-pick **`Fixes`** for multiple issues; default narrative is **`Refs`**-style **only when** the user explicitly chose minimal keyword lines for several refs.

**Hand-off:** Pass a compact table or list (issue #, evidence source, suggested link mode: **minimal keyword** / **UI**) to **`@gh-pr`** **§9**; **`read-shuttle-gh-pr-commands`** owns shuttle commands after **Proceed**.

---

## 7. Title + body + triple pass

- Draft per **`read-pr-content`**, **`$PR_TEMPLATE_SOURCE`/`$PR_TEMPLATE_BODY`**, and **`section-patterns`** when canonical. **Full replace** vs **`$BASE_GIT`**; no compare-header noise (SHAs, commit counts).
- **Issue linkage in the posted body:** **No** default **“Linked issues”** markdown section from §6.6. **Default:** omit **`Refs` / `Fixes` / `Closes`** lines from the draft body. Add **at most one minimal trailing line** of **`Refs #n` / `Fixes #n` / `Closes #n`** only when the user already chose the **keyword path** in chat **or** the draft is being revised **after** **`@gh-pr`** **§9** narrowed linkage (see §6.5 and **`read-shuttle-gh-pr-commands`**). For multiple candidates without a clear choice, keep keywords **out** of the body and carry candidates in the **§9** prompt (keywords or UI-only). See **[`read-pr-body-sections/section-patterns`](../pr-body-sections/section-patterns/SKILL.md)** and **[`pr-body-skeleton`](../pr-content/pr-body-skeleton/SKILL.md)**.
- **Triple pass:** (1) TL;DR + outline cover §6 themes by concern? (2) form (lists, tables only when tiny)? (3) claims match §6 **and** any optional keyword line matches the **§9** mutation summary (issue numbers + **`Refs`** vs **`Fixes`/`Closes`**) before **`gh pr`** runs? Hand title/body to **`@gh-pr`** §9.

### Existing PR as template

When **`PR_NUM`** is set: reuse **voice** / **headings** / **emoji cadence** from the open PR body only—rebuild **facts** from §6; do not treat the old body as authority for paths or behavior.

### Title

**[`title-line`](../pr-content/title-line/SKILL.md)** — plain text, no emoji.

### Body — canonical structure

**[`read-pr-body-sections/section-patterns/SKILL.md`](../pr-body-sections/section-patterns/SKILL.md)** — normative when **`canonical`** or when normalizing.

---

## Do not

- PR mutation or **Proceed** for **`gh pr create`/`edit`** (parent §9).
- Skip **`read-repo-forms-json`** when Step A applies and **`gh`** is expected.

## See also

- [`read-repo-forms-json`](../repo-forms-json/SKILL.md)
- [`read-repo-stream`](../repo-stream/SKILL.md)
- [`read-shuttle-gh-issue-read`](../../shuttle/gh/issue-read/SKILL.md)
- [`read-shuttle-gh-pr-commands`](../../shuttle/gh/pr-commands/SKILL.md)
- [`@gh-pr`](../../../gh/pr/SKILL.md)
