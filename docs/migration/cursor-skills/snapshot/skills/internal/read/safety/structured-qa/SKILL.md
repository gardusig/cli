---
name: read-safety-structured-qa
description: >-
  Read-only: AskQuestion vs chat, short labels, ordering, one freeform outlet; §0 write gate (question + options libs);
  §1e Abort/Review/Proceed for offline outside-repo + online writes; §1f PR/issue identifier display. Pairs with
  read-safety-skill-safety (which ops need confirm). Does not replace parent skill content.
---
# Internal: Structured Q&A (`read-safety-structured-qa`)

**Read-only policy library.** Skills that **ask**, **confirm**, or offer **finite choices** in Cursor apply **§1–§8** here (**§1** includes **§1e** triage). **Write libraries** (`skills/internal/write/<domain>/**`): the **caller** (usually a public **`@git-*` / `@gh-*`** skill) must run the **write gate** (**§0**) before any fence in a **`write/`** library—**never** “chat yes” alone.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do not

- Replace **`read-safety-skill-safety`** wholesale.
- Embed **AskQuestion orchestration** in public **`@git-*` / `@gh-*`** skills — link **§0 write gate** only.

---

## 0. Write gate — before every mutation

**Normative for all mutating work.** Public skills **orchestrate workflow order** only; **prompt UX lives here** and in the child libraries below.

### 0a. Fixed sequence

1. **Summary (chat)** — **[`read-safety-structured-qa-summary`](./summary/SKILL.md)**: goal, targets, counts, **#n — title** rows, diff stat, what runs on confirm. **Not** inside the AskQuestion prompt.
2. **Question** — **[`read-safety-structured-qa-question`](./question/SKILL.md)**: one short English **`prompt`** string.
3. **Options** — **[`read-safety-structured-qa-options`](./options/SKILL.md)**: safe-first finite labels mapping to exact actions.
4. **AskQuestion** — invoke with outputs from steps 2–3; **one** freeform outlet per **§5**.
5. **Proceed** — on affirmative choice only → run **`write-*`** fences (or the next orchestration step the gate unlocked).

Repeat the gate when scope changes or a new mutation phase starts. **Do not** merge unrelated risks into one **Proceed**.

### 0b. Public `@git-*` / `@gh-*` boundary

- **Do** — state **when** a write gate is required; list **`read-safety-structured-qa`** (+ domain preflight libraries) under **Required internal skills**; verify **Proceed** happened before mutations.
- **Do not** — spell out AskQuestion prompt text, option label lists, or modal shape in public skill bodies (**On invoke**, **Do**, **Verification**). Domain-specific gather/clarify lists stay in **`read-*-preflight-qa`** libraries.
- **Read-only** public skills — no write gate unless finite disambiguation is needed (**§1e** last paragraph).
- **Recommended next steps** after **Verification** — delegate to **[`read-skill-suggestions`](../../skill-suggestions/SKILL.md)** only; no inline AskQuestion orchestration.

### 0c. Write library boundary

Every **`skills/internal/write/**`** leaf states: **caller owns write gate (§0) before mutating blocks**. Write libraries **never** invoke AskQuestion themselves.

---

## 1. Finite choices — structured UI first

- Use **AskQuestion** (or equivalent) for small known outcome sets; **gather facts** (names, dry-run) **before** options.

### 1a. Order: summary → question → options → one chat line

1. **Summary** — in the **assistant message immediately above** AskQuestion (not inside the modal prompt). Goal line + tight facts (`git status --short`, `git diff --stat`, counts, top paths, commit intent—whatever parent requires). **Detail lives here**; labels stay tiny.
2. **Question** — one short sentence in the AskQuestion **prompt** (“Proceed with …?” / “Which PR should be updated?”). **≤ ~120 characters** when practical.
3. **Structured options** — real finite set only; no fake **Other…** if §5 chat line covers escape (**§5**). Put identifiers and titles here—not in the prompt.
4. **One** trailing chat invite max (**§5**).

### 1b. Minimal binary (low-risk doc apply)

Short summary (~5 bullets) → one-line question → **No**/**Yes** (**No** first) → optional trailing line (omit when noisy; **keep** for §3a triggers).

### 1c. Bulk preview (bulk / non-trivial writes)

Summary + file count + paths → “Proceed?” → **No**/**Yes** (**No** first). **Yes** = execute as summarized. **Large** commit+push: **one** combined **No**/**Yes** with **`read-safety-skill-safety`**—do not stack duplicate modals for the same phase.

### 1d. Pre-write and mutation prompts (brief question, summary above)

For prompt gates that immediately decide a write path (for example, choose edit/create before drafting, or confirm a final GitHub mutation):

1. Put the **full actionable summary** in the assistant message immediately before AskQuestion (goal, target, key facts, what happens on Proceed).
2. Keep the **AskQuestion prompt text short** (one sentence; identifiers and action only). Do not paste full PR/issue bodies, long diffs, or large markdown blocks in the prompt itself.
3. Use safe-first options: **Abort** first, then one or more **Proceed** options that map to exact actions.
4. Offer exactly one refinement outlet per **§5** (either **`additionalSuggestion`** or one trailing chat line, not both).
5. If multiple **Proceed** options exist, keep labels short and specific (for example, “Proceed — edit #n”, “Proceed — create new”).

**`@gh-issue` multi-issue batch:** When several themes ship in one invocation, put a compact **table** in the pre-prompt summary (theme → **edit #n** or **create** → body file path if any). Offer **Abort** (safe-first), optional **Defer** / narrow options if the parent skill allows, then **Proceed — batch** whose summary already lists **every** `gh issue create` / `gh issue edit` in execution order. **One** Proceed confirms the **whole** batch. If the user prefers smaller steps, stop after partial execution and route remaining themes to a **follow-up `@gh-issue`** (new summary + Proceed).

This pattern complements **§3a** and is commonly used in **`@gh-pr`** intent and mutation confirms.

### 1f. PR and issue identifiers in Q&A

When disambiguating or confirming GitHub PRs or issues:

1. **Summary (chat above the modal)** — compact table or bullets: **#n — title** (optionally **head → base**, labels, or one-line match reason). Link the **#n** in markdown when a URL is known. **Do not** paste PR/issue **body**, long descriptions, or diff hunks here unless the user explicitly asked to review that text.
2. **AskQuestion prompt** — one short action question only (for example, “Update an existing PR or create a new one?”). **Never** embed PR titles, bodies, or match evidence in the prompt string.
3. **Option labels** — **#n — title** or **Proceed — edit #42**; keep each label **≤ ~80 characters** (truncate long titles with `…`). **Do not** repeat the PR/issue body in options.
4. **Language** — English labels per **[`read-safety-language-interaction-rules`](../language-interaction-rules/SKILL.md)**.

**Good**

- Summary: `| PR | head → base |` with `[#42](url) — fix structured Q&A prompts | feature/x → main |`
- Prompt: “Which PR should be updated?”
- Options: `Abort` · `#42 — fix structured Q&A prompts` · `Create new PR`

**Bad**

- Prompt: “Found open PR #42 ‘fix structured Q&A prompts’ from feature/x with body: …”
- Options with full PR markdown body or multi-line issue text.

**`@gh-issue` pre-dedupe gate:** after each issue-draft refinement summary, use **Sharpen / Abort / Ship** (finite labels, **§5**) before inventory/dedupe; orchestration lives in **[`read-issue-preflight-qa`](../issue/preflight-qa/SKILL.md)**.

### 1e. Pre-write triage — offline outside repo + online mutations

When **`read-safety-skill-safety`** applies to **writes outside the git workspace root** or **online mutations** (remote GitHub changes, **`git push`**, durable **`gh`** writes, tag push to **`origin`**, …):

1. **Summary first** — **Goal** + targets + counts per **§1a**; use **§1c** when bulk/large or many paths.
2. **AskQuestion** (safe-first order when labels are ordered): **Abort** / **Review** / **Proceed**.
   - **Abort** — stop; no mutating fence.
   - **Review** — pause to restate targets, paths, or intent in chat; adjust destination/repo/title/body **without** running **`gh`**, **`git push`**, **`git archive`**, or other mutating blocks yet. Then re-summarize and ask again.
   - **Proceed** — execute **exactly** what was summarized.

This tri-modal gate is for **writes only**. **Read-only** work (**`gh` list/view/search** when non-mutating, **`read-repo-stream`**, reading paths outside the workspace for **inspection**) stays **straightforward**: optional tight **§1a** preamble, then run the read **without** stacking **Abort / Review / Proceed**. Use **AskQuestion** on reads only for **finite disambiguation** (for example which issue id), not as mandatory safety triage.

**Relation to §8:** **Review** overlaps **Change approach** in failure triage—prefer the same short labels across flows.

---

## 2. Option design

- **Very short labels** — **No**/**Yes**, **Abort**/**Proceed**, or verb+object; optional ~80-char template hint.
- **~2–12** options; larger sets → narrow first.
- **Never** paragraphs inside option text.

---

## 3. Destructive / binary flows

- Opposing actions clear; **impact before confirm** (`git status`, dry-run, counts).
- **Default-safe:** ambiguous → abort unless parent says otherwise.
- **One confirm per major risk**—do not merge unrelated risks into one **Yes**.

### 3a. Goal-first (safety triggers)

For ops flagged in **`read-safety-skill-safety`** (commit, push, reset/clean, destructive installs, **`gh`** PR/issue mutations, bulk deletes, writes outside repo, …):

1. **Preamble** — **Goal** (one line) + compact facts (**§1a**).
2. **Question** — one short sentence (e.g. “Proceed with commit and push?”).
3. **AskQuestion** — **No**/**Yes** or **Abort**/**Proceed**; safe option first when order matters.
4. **One** chat reminder after buttons (**§5**); skip if redundant with **`additionalSuggestion`**.

The modal prompt may repeat only minimal identifiers (branch/tag/target), while the detailed summary remains in the message above.

Remote irreversible (**push**, durable **`gh`** writes) and local destructive (**reset/clean**, wipes) share this pattern.

---

## 4. Open-ended

Chat prompt; one question + inline examples; re-ask with constraint on validation failure (e.g. branch name).

---

## 5. Freeform — no duplicate outlets

- **Safest option first** when UI order matters.
- **Escape** = real negative options (**No**/**Abort**)—not **Other…** **and** “or type in chat” **and** **`additionalSuggestion`** same turn.
- **One** freeform outlet: either **one** post-button chat line **or** JSON **`additionalSuggestion`**—not both as duplicate “type something else” paths.
- **`allow_multiple: true`** only when truly needed (rare).

---

## 6. Tool naming

Describe capability (“structured multiple-choice”) vs hard-coding a single IDE control name.

---

## 7. Consumers (index)

**Write gate (§0):** every mutating public **`@git-*` / `@gh-*`** skill — **summary** via **[`read-safety-structured-qa-summary`](./summary/SKILL.md)**, **question** via **[`read-safety-structured-qa-question`](./question/SKILL.md)**, **options** via **[`read-safety-structured-qa-options`](./options/SKILL.md)**.

**Any** skill with destructive **Proceed**: **`@git-push`**, **`@git-main`**, **`@git-reset`**, **`@git-start`**, **`@git-review`** (install prepare), **`@git-docs`**, **`@git-tag`**, **`@git-cherry-pick`**, **`@git-revert`**, **`@git-rebase`**, **`@gh-pr`**, **`@gh-pr-close`**, **`@gh-issue`**, **`@gh-issue-close`**, **`@gh-issue-delete-closed`**, **`read-pr-description`** (multi-template / material reshape), **large** doc edits (**`read-safety-skill-safety`** **confirm-first**).

**Post-verify suggestions only (not write gates):** **`@gh-issue-pick`**, **`@gh-issue-review`** (scope), **`read-skill-suggestions`** **§9** — optional next-step AskQuestion after **Verification**, not before mutations.

**Internal:** **`read-safety-skill-safety`** — trigger list vs **§0** / **§3a** / **§1e** here.

---

## 8. Failure triage

Use this pattern when a mutating step fails (for example **`git push`**, **`gh`** mutation), or when a new fact changes the approach (for example wrong branch, missing remote, protected/default-branch restrictions).

1. Put full failure context in the assistant message above the prompt. Keep AskQuestion prompt brief and action-oriented (for example, “Push failed on branch `foo`; choose next step.”).
2. Keep options to about **3** when possible, **safe-first**:
   - **Abort** — stop without further writes.
   - **Change approach** — switch tactic (for example create/switch branch, choose a different target, or refine in chat per **§5**).
   - **Proceed / Retry** — retry same path; if risky (for example force-like behavior), name the risk in the label/prompt.
3. Do not hide risky actions behind generic “Proceed.” If an option can rewrite shared history or bypass protection, call that out explicitly and rely on **`read-safety-skill-safety`** triggers.
4. Keep one refinement outlet only (either **`additionalSuggestion`** or one trailing chat line), consistent with **§5**.

---

## 9. Recommended next steps — public `@git-*` / `@gh-*`

Use **after** the skill’s main work and **Verification** checklist—**not** a write gate and **not** before mutations complete.

### 9a. `skip` runtime flag (required)

| Value | When | Suggestions |
| --- | --- | --- |
| **`skip=false`** | Root user invoked the public skill (for example user typed **`@git-tag`**) | **Offer** optional next-step choices via **[`read-skill-suggestions`](../skill-suggestions/SKILL.md)** when **§9b** applies |
| **`skip=true`** | Nested **public** skill call from another public skill (middle of a chain) | **Do not** offer next-step AskQuestion — parent owns suggestions when **its** chain finishes |

**Examples:** **`@git-tag`** → **`@git-push`** (**`skip=true`**) → **`@git-main`** (**`skip=true`**) → back to **`@git-tag`** (**`skip=false`** at root) → then suggest **`@git-branch-delete-all`**, etc.

Pass **`skip=true`** on every nested child public-skill invocation. Only the skill the **user** invoked stays **`skip=false`**.

### 9b. ENV bypass flags (each public skill documents its own)

| Flag | Effect |
| --- | --- |
| **`SKIP_QA_<SKILL>=true`** | Bypass routine **write gates** for that public skill (high-risk confirms may still apply) |
| **`SKIP_QA_WRITE=true`** | Shared bypass for routine write-flow Q&A where the parent skill allows |
| **`SKIP_SUGGESTIONS=true`** | Suppress **§9** next-step prompting even when **`skip=false`** at root |

Default: all unset/false → write gates active; suggestions offered at root when **Verification** passes.

### 9c. When to offer suggestions (`skip=false` only)

1. **Verification** checklist satisfied for the current skill.
2. User has **not** already named the next skill or declined further work.
3. **`SKIP_SUGGESTIONS`** is not set.
4. A **clear** next step remains — rank from **[`read-skill-suggestions`](../skill-suggestions/SKILL.md)** (**summary** → **options** → one AskQuestion).

### 9d. Shape

- Pre-question **summary** — **[`read-skill-suggestions-question-summary`](../skill-suggestions/question-summary/SKILL.md)**.
- **Options** — **[`read-skill-suggestions-qa-alternative-options`](../skill-suggestions/qa-alternative-options/SKILL.md)** + **[`read-skill-suggestions-next-steps-options`](../skill-suggestions/next-steps-options/SKILL.md)** catalog.
- **2–4** finite public **`@…`** choices plus **Done** / **Not now** (safe-first).
- **Do not** auto-run suggested skills without a new user choice.

Each public **`SKILL.md`** uses **`## Skip & suggestions`** (ENV flags + **`skip`**) and **`## Recommended next steps`** pointing at **`read-skill-suggestions`**.

## See also

- [`read-safety-structured-qa-summary`](./summary/SKILL.md)
- [`read-safety-structured-qa-question`](./question/SKILL.md)
- [`read-safety-structured-qa-options`](./options/SKILL.md)
- [`read-safety-skill-safety`](./skill-safety/SKILL.md)
- [`read-skill-suggestions`](../skill-suggestions/SKILL.md) — post-verify **§9** suggestions
