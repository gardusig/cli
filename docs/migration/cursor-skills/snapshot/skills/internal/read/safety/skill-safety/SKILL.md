---
name: read-safety-skill-safety
description: >-
  Read-only: which operations need summary → confirm → act (push, commit, deletes, reset/clean, bulk/structural
  creates, writes outside repo root, system-wide toolchain changes when the agent would perform them); §1e triage for
  writes vs lightweight reads. Does NOT replace parent skills—layers on read-safety-structured-qa for prompt UX.
---
# Internal: Skill safety (`read-safety-skill-safety`)

**Read-only policy.** Skills that perform **irreversible** or **high-impact** work must **summarize impact**, then **obtain explicit user confirmation**, then **act**. Confirmation UX follows **[`read-safety-structured-qa`](../structured-qa/SKILL.md)** **§1a**, **§1b**, **§1c**, **§1e**, **§2**, **§3–§3a**, **§5**, **§8**.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Internal libraries: read vs write cadence

- **Read-only internals** — Non-mutating **`read-repo-*`**, **`read-workflow-git-*`** playbooks; read-only parents may skip extra confirm unless disambiguation is needed. **Never** skip **Proceed** on later **`gh`** / **`git`** mutations.
- **Write / mutation internals** — **`write-*`**, **`write-workflow-git-*`** fences always run behind a public skill with **Goal + structured confirm** first.

## `read/gh` vs `git` work

- **`read/gh`** — **`gh`** inventory, templates, issue/PR shapes.
- **`read/git`** + **`write/git`** — local **`git`** fences, sync, merge playbooks, tag/commit/align.
- **Public** **`@git-*`** / **`@gh-*`** own user intent; they link **`read-safety-structured-qa`** + **`read-safety-skill-safety`** for confirms.

---

## Pattern

1. **Summarize** — per **`read-safety-structured-qa`** **§1a**; **§1c** when bulk/large.
2. **Write gate** — **`read-safety-structured-qa` §0** (**question** → **options** → **Proceed**); merge **§1c** + **§3a** into **one** gate when both apply.
3. **Act** — only after **Yes** / **Proceed**, or explicit chat alternative (re-summarize if scope changed).

**Structured confirm** — Meet the relevant **Triggers** row **and** apply **`read-safety-structured-qa`** **§0** + **§1c** + **§3a** / **§1e**. Link **this file** once per skill; then **write gate** is enough shorthand.

---

## Triggers (minimum)

| Trigger | Summary must include | Confirm |
| --- | --- | --- |
| **`git push`** / tag push to **`origin`** | Branch or tag, remote intent, stat if dirty | Yes, before commit (if any) and push |
| **`git push --force-with-lease`** | Branch, remote, risk, alternatives | Yes — separate from normal push |
| **`gh issue delete`** (bulk) | Count + preview table | Yes, before each wave |
| **`git commit`** | Stat / message intent | Yes (may share with push) |
| **`gh pr create` / edit / close`** | Repo, refs, PR #, intent | Yes, before mutation |
| **`gh label create`** | Label names, colors | Yes (may be separate from issue create) |
| **Delete** paths | Count + paths | Yes |
| **`git reset --hard`**, **`git clean`**, destructive installs | Dry-run / impact | Yes |
| **Bulk / structural creates** | Count + top paths | Yes |
| **Writes outside repo root** | Paths named; Goal | Yes — **§1e** |
| **Large change set** | **§1c** bulk preview in preamble | Yes — merge with commit/push when both apply |

**Large change set** — **≥10 files** or **≥500** net diff lines (parent may tighten).

### Exception: **`@git-pull`** merge commits

No separate **AskQuestion** per merge commit when finishing **`@git-pull`**. Unexpected dirty tree → stop per **`read-safety-structured-qa`** **§4**.

### Exception: ephemeral scratch in **`@git-push`**

Removing throwaway paths created in the same **`@git-push`** run (never staged) does **not** need separate confirm.

---

## Scope for new files (“create”)

- **No** extra confirm for routine single-file edits the user asked for.
- **Yes** for bulk/structural adds or many in-place doc edits (**`@git-docs`** **§1c**).

---

## Cross-skill Q&A (quick map)

| Situation | Skill / library |
| --- | --- |
| Many new doc paths | **Large create** — confirm before bulk writes |
| **`@git-docs`** (existing files) | Mode AskQuestion; **§1c** before bulk in-place |
| Commit + push | **`@git-push`** |
| **`gh` PR / issue mutations | **`@gh-pr`**, **`@gh-issue`**, close/delete skills |
| Issue → branch → PR | **`@gh-issue-view`** → **`@git-start`** → **`@gh-pr`** with confirms |

---

## Do

- Apply triggers; link **`read-safety-structured-qa`** for how to ask.
- **One confirm per major risk**.

## Do not

- Skip summary or confirmation for table rows.
- Treat ambiguity as consent—default **abort**.

---

## See also

- [`read-safety-structured-qa`](../structured-qa/SKILL.md)
