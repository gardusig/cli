---
name: read-issue-labels-label-decorate
description: >-
  Read-only: gh label list/match/create command shapes. Parent read-issue-labels.
---
# Issue labels — decorate (examples)

Used by **[`read-issue-labels`](./SKILL.md)** and **`@gh-issue`**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Example A — Map to existing labels

**Input (chat):** “Add label guidance for skills pack; touch `skills/internal/read/issue/` and templates.”

**Draft title:** `Document issue label heuristics for skill repos`

**Draft body (excerpt):** “… acceptance: label list command, 0–3 labels, confirm before `gh label create` …”

**Step:** Existing labels include `documentation`, `enhancement`.

**Output (proposal table):**

| Candidate | Action | GitHub label |
| --- | --- | --- |
| docs / templates | reuse | `documentation` |
| feature work | reuse | `enhancement` |

**Attach (preview):** use [`read-shuttle-gh-issue-commands`](../../../../read/shuttle/gh/issue-commands/SKILL.md) with `--label "documentation,enhancement"` after **Proceed**.

---

## Example B — One new label, then attach

**Input:** “Track flaky CI on `gh-pr` skill; file an issue.”

**Draft title:** `Flaky CI when running gh-pr orchestration tests`

**Existing labels:** `bug`, `ci` (no `area:gh`).

**Step:** Propose **`ci`** + **`bug`**; suggest **`area:gh`** as **new** (repo has other `area:*` labels).

**Output:**

| Candidate | Action | Notes |
| --- | --- | --- |
| CI | reuse | `ci` |
| defect | reuse | `bug` |
| domain | **create** | `shuttle gh label create area:gh --color ededed --description "GitHub PR CLI skills" --yes` → **structured confirm** first |

**Then create issue:** [`read-shuttle-gh-issue-commands`](../../../../read/shuttle/gh/issue-commands/SKILL.md) with labels after **Proceed**.

---

## Do not

- Attach **more than three** labels without explicit user ask.
- Create labels that only duplicate an existing name with different spelling.
