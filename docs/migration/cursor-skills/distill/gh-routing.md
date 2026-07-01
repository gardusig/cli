# GitHub skills wiki (`@gh-*`)

Single-page wiki for **`gh`** / GitHub API orchestrators. Normative behavior lives in each linked **[`SKILL.md`](../skills/gh/)**; **deterministic GitHub I/O** runs through **[shuttle-cli](https://github.com/gardusig/shuttle-cli)** `shuttle gh` (see [shuttle integration](#shuttle-cli-integration)).

**Related:** [Wiki hub](README.md) · [Read libraries](read.md) · [Write libraries](write.md) · **Invoke graph:** [README.md#public-skills](README.md#public-skills) · [`read-shuttle-gh`](../skills/internal/read/shuttle/gh/SKILL.md)

---

## Contents

1. [Skill catalog](#skill-catalog)
2. [Shuttle-cli integration](#shuttle-cli-integration)
3. [Deterministic routing](#deterministic-routing)
3. [Issues — CRUD map](#issues--crud-map)
4. [Issues in this pack](#issues-in-this-pack)
5. [Pull requests in this pack](#pull-requests-in-this-pack)
6. [Workplace and Q&A](#workplace-and-qa)
7. [Dependencies](#dependencies)
8. [Read/write artifacts](#readwrite-artifacts-normative-prose)
9. [Safe changes](#safe-changes)

---

## Skill catalog

| Invoke | Summary | `SKILL.md` |
| --- | --- | --- |
| **`@gh-pr`** | PR discovery, delta narrative, create/edit; skill-pack body guidance for **`skills/**`** / **`docs/**`**. Assumes head commits are already on the remote. | [`skills/gh/pr/SKILL.md`](../skills/gh/pr/SKILL.md) |
| **`@gh-pr-list`** | Read-only **`gh pr list`** / inventory shapes. | [`skills/gh/pr/list/SKILL.md`](../skills/gh/pr/list/SKILL.md) |
| **`@gh-pr-view`** | Read-only **`gh pr view`** / diff stat. | [`skills/gh/pr/view/SKILL.md`](../skills/gh/pr/view/SKILL.md) |
| **`@gh-pr-review`** | AI acceptance review vs linked issues; read-only on GitHub. | [`skills/gh/pr/review/SKILL.md`](../skills/gh/pr/review/SKILL.md) |
| **`@gh-pr-close`** | Close a PR after structured confirm. | [`skills/gh/pr/close/SKILL.md`](../skills/gh/pr/close/SKILL.md) |
| **`@gh-issue`** | Router: preflight + **Sharpen / Abort / Ship** + dedupe + one confirmed create-or-edit path. | [`skills/gh/issue/SKILL.md`](../skills/gh/issue/SKILL.md) |
| **`@gh-issue-execute`** | Execute approved issue checkpoints with verification evidence and PR handoff. | [`skills/gh/issue/execute/SKILL.md`](../skills/gh/issue/execute/SKILL.md) |
| **`@gh-issue-backlog`** | Sorted epic/child backlog tree via `shuttle gh backlog tree`. | [`skills/gh/issue/backlog/SKILL.md`](../skills/gh/issue/backlog/SKILL.md) |
| **`@gh-issue-next`** | Lowest open child by sequence → view → execute handoff. | [`skills/gh/issue/next/SKILL.md`](../skills/gh/issue/next/SKILL.md) |
| **`@gh-issue-labels`** | Label manifest sync, inventory, labelize batch. | [`skills/gh/issue/labels/SKILL.md`](../skills/gh/issue/labels/SKILL.md) |
| **`@gh-issue-review`** | Read-only reshape: discovery, view, peer list, gaps, AskQuestion. | [`skills/gh/issue/review/SKILL.md`](../skills/gh/issue/review/SKILL.md) |
| **`@gh-issue-list`** | Read-only list/search inventory. | [`skills/gh/issue/list/SKILL.md`](../skills/gh/issue/list/SKILL.md) |
| **`@gh-issue-view`** | Read-only single issue (URL / `#n`). | [`skills/gh/issue/view/SKILL.md`](../skills/gh/issue/view/SKILL.md) |
| **`@gh-issue-pick`** | List open issues + AskQuestion to pick next task. | [`skills/gh/issue/pick/SKILL.md`](../skills/gh/issue/pick/SKILL.md) |
| **`@gh-issue-delete-closed`** | Bulk **`gh issue delete`** for closed issues after confirm. | [`skills/gh/issue/delete/closed/SKILL.md`](../skills/gh/issue/delete/closed/SKILL.md) |
| **`@gh-issue-close`** | Soft-close an issue after confirm. | [`skills/gh/issue/close/SKILL.md`](../skills/gh/issue/close/SKILL.md) |

---

## Shuttle-cli integration

**Split:** cursor-skills **`@gh-*`** skills decide *what* to do (dedupe, split/merge proposals, AskQuestion gates). **[shuttle-cli](https://github.com/gardusig/shuttle-cli)** runs *deterministic* GitHub commands via **`shuttle gh …`** (JSON output, write gates, **`--yes`** after Cursor **Proceed**).

| Layer | Tool |
| --- | --- |
| Agent judgment | `@gh-issue`, `@gh-issue-review`, `read-issue-dedupe`, … |
| Terminal / GitHub I/O | `shuttle gh issue list`, `shuttle gh issue create`, `shuttle gh pr create`, … |

**Contract:** [`read-shuttle-gh`](../skills/internal/read/shuttle/gh/SKILL.md) — full command map and migration status.

**Implementation:** [shuttle-cli epic 01](https://github.com/gardusig/shuttle-cli/issues/34) (`01 — GitHub integration` + children **01a–01i**) — foundational layer alongside `shuttle git` and `shuttle docker`.

**Tooling:** `shuttle` on PATH + authenticated `gh`. Public skills invoke **`shuttle gh …`** via [`read-shuttle-gh-*`](../skills/internal/read/shuttle/gh/SKILL.md) libraries — not raw `gh` bash fences.

**Planning:** use chat/planning for goals — **not** a separate planning skill. Skills recommend outcomes; shuttle executes defined GitHub ops.

**Label catalog (target repos):** [`.cursor/gh/labels.manifest.yaml`](../.cursor/gh/labels.manifest.yaml) — synced via `shuttle gh label sync --manifest …`.

---

## Deterministic routing

- If the user asks to **discover improvements** or refine a backlog, use **chat/planning** then **`@gh-issue`** on **Ship to issues** (or **`@gh-issue-backlog`** to inspect order).
- If the user asks to **pick the next work item**, route to **`@gh-issue-next`** (or **`@gh-issue-pick`** for manual choice).
- If the user asks to **plan execution from a specific issue**, use issue body + chat checkpoints then **`@gh-issue-execute`**.
- If the user asks for **read-only issue/PR inventory**, route to `@gh-issue-list`, `@gh-issue-view`, `@gh-issue-pick`, `@gh-pr-list`, or `@gh-pr-view`.
- If the user asks to **create or update issue content**, route to `@gh-issue` (preflight + **Sharpen / Abort / Ship**, then list/dedupe, then one confirmed mutation path).
- If the user asks to **close/delete issues**, route to `@gh-issue-close` or `@gh-issue-delete-closed` with Goal + Proceed gates.
- If the user asks to **create/edit PR content**, route to `@gh-pr` (preflight → description → confirmed create/edit).
- If the user asks to **review a PR (AI)**, route to **`@gh-pr-review`**.
- If the user asks to **merge a PR**, direct them to the **GitHub UI** after **`@gh-pr-review`** or **`@gh-pr-view`**; confirm merged state with **`@gh-pr-view`**.
- If the user asks to **close PRs**, route to `@gh-pr-close` with explicit confirmation.

### Canonical three-loop method

1. **Ideas to issues (iterative):** chat/planning → **`@gh-issue`** until backlog themes are filed.
2. **Issue to PR (per selected issue):** **`@gh-issue-next`** / **`@gh-issue-pick`** / **`@gh-issue-view`** → **`@gh-issue-execute`** → **`@gh-pr`** → **`@gh-pr-view`**.
3. **PR to merge (per selected PR):** `@gh-pr-review` (optional) → merge in **GitHub UI** → `@gh-pr-view` (confirm merged).

---

## Issues — CRUD map

| Op | Skill | Notes |
| --- | --- | --- |
| **Review / reshape (read-only)** | **`@gh-issue-review`** | Discover repo → view **`#n`** → list/search peers → overlap + gaps → **AskQuestion** |
| **Create or update** | **`@gh-issue`** | Preflight + **Sharpen / Abort / Ship** → dedupe → one confirmed edit/create path |
| **Read** | **`@gh-issue-list`**, **`@gh-issue-view`**, **`@gh-issue-pick`** | List/search; detail / URL / **`#n`**; triage + AskQuestion |
| **Close** | **`@gh-issue-close`** | Soft-close |
| **Delete (closed bulk)** | **`@gh-issue-delete-closed`** | Hard delete — **Goal + preview + Proceed** |

**Local notes with an issue (optional):** [`ISSUE_CONTEXT.md`](../skills/internal/read/issue/description/issue-context/SKILL.md)

---

## Issues in this pack

- **`@gh-issue-review`** — read-only pass when an issue needs **codebase context**, **duplicate checks**, and a **clearer description draft** before editing.
- **`@gh-issue`** — router entry: **Sharpen / Abort / Ship** → **list → dedupe → confirmed create-or-edit**.
- **`@gh-issue-execute`** — checkpoint execution lane before PR creation.
- **`@gh-issue-backlog`** / **`@gh-issue-next`** — ordered backlog and next-child pick via **`shuttle gh backlog`**.
- **`@gh-issue-labels`** — manifest sync and label hygiene via **`shuttle gh label`**.
- **Discovery loop:** chat/planning → **`@gh-issue`** → **`@gh-issue-execute`** / **`@gh-issue-next`**.
- **Grooming loop:** **`@gh-issue-list`** / **`@gh-issue-pick`** → **`@gh-issue-view`** → **`@gh-issue`** / **`@gh-issue-close`** as needed.

### Preflight and delivery

- **Drafts:** chat and optional **`.cursor/gh/issue/<slug>.md`** before **`gh issue create`**.
- **Plan + delivery (full):** **`@gh-issue-view`** → **`@gh-issue-execute`** → **`@gh-pr`** → **`@gh-pr-view`** → merge in GitHub UI.
- **Delivery (lightweight):** **`@gh-issue-view`** → implement (out of pack) → **`@gh-pr`**.

---

## Pull requests in this pack

- **`@gh-pr`** — supported path for PR **create/edit** after preflight and description work; includes skill-pack body guidance when the change set is mostly **`skills/**`** / **`docs/**`**.
- **`@gh-pr-list`** / **`@gh-pr-view`** — read-only inventory and inspection.
- **`@gh-pr-review`** — AI acceptance review vs linked issues.
- **`@gh-pr-close`** — closes a PR only after explicit structured confirm.

**Merge:** not a public skill in this pack — use the GitHub UI after review; confirm with **`@gh-pr-view`**.

### Improvement flow requirements

1. **Issue context settled** (scope + acceptance clear)
2. **Execution checkpoints completed** (`@gh-issue-execute`)
3. **PR created and reviewed** (`@gh-pr` + `@gh-pr-view` / `@gh-pr-review`)
4. **Merge confirmed** (GitHub UI + **`@gh-pr-view`**)

**PR shapes (`read-pr-content`):** [`PR_ORCHESTRATION.md`](../skills/internal/read/pr/content/pr-orchestration/SKILL.md), [`BODY_SKELETON.md`](../skills/internal/read/pr/content/pr-body-skeleton/SKILL.md), [`TITLE_LINE.md`](../skills/internal/read/pr/content/title-line/SKILL.md).

---

## Workplace and Q&A

**Public skill shape:** **`## Language interaction policy`** → **`## Before batch`** → **`## Required internal skills`** → body → **`## Verification`** → **`## Recommended next steps`**. Details: [`docs/onboarding.md`](onboarding.md).

If **`gh`** is unavailable, you cannot run **`@gh-*`** end-to-end. Use the **GitHub web UI** and reuse title/body artifacts under **`skills/internal/read/issue/`** and **`skills/internal/read/pr/`**.

1. **Online / mutating** (`gh issue create`, `gh pr create`, …) — **Goal + structured Q&A + Proceed**.
2. **Read-only** `gh` for dedupe/list/search — no confirmation by default; **`@gh-issue-pick`** uses AskQuestion for **which issue** only.

---

## Dependencies

[`skills/internal/read/issue/*`](../skills/internal/read/issue/), [`skills/internal/read/pr/*`](../skills/internal/read/pr/), [`skills/internal/read/shuttle/gh`](../skills/internal/read/shuttle/gh/SKILL.md), [`skills/internal/read/workflow/*`](../skills/internal/read/workflow/) (including **structured-qa**, **skill-safety**), [`skills/internal/write/issue/*`](../skills/internal/write/issue/), [`skills/internal/write/pr/*`](../skills/internal/write/pr/). Library indexes: **[`read.md`](read.md)**, **[`write.md`](write.md)**. External: **[shuttle-cli](https://github.com/gardusig/shuttle-cli)**.

---

## Read/write artifacts (normative prose)

| Topic | File |
| --- | --- |
| Issues orchestration (`@gh-issue`) | [`read-issue-dedupe`](../skills/internal/read/issue/dedupe/SKILL.md) |
| Issue body skeleton | [`BODY_SKELETON.md`](../skills/internal/read/issue/description/issue-body-skeleton/SKILL.md) |
| PR orchestration (`@gh-pr`) | [`PR_ORCHESTRATION.md`](../skills/internal/read/pr/content/pr-orchestration/SKILL.md) |
| PR body skeleton | [`BODY_SKELETON.md`](../skills/internal/read/pr/content/pr-body-skeleton/SKILL.md) |
| PR delta narrative | [`delta-narrative`](../skills/internal/read/diff/summary/delta-narrative/SKILL.md) |

---

## Safe changes

Wording and links aligned with **`skills/gh/**/SKILL.md`**; do not duplicate command matrices here.

## Coverage matrix

| Intent | Primary skill |
| --- | --- |
| Issue create/edit router | `@gh-issue` |
| Issue read/review/pick | `@gh-issue-list`, `@gh-issue-view`, `@gh-issue-review`, `@gh-issue-pick` |
| Issue close/delete | `@gh-issue-close`, `@gh-issue-delete-closed` |
| Issue backlog / labels | `@gh-issue-backlog`, `@gh-issue-next`, `@gh-issue-labels` |
| PR create/edit | `@gh-pr` |
| PR list/view/review/close | `@gh-pr-list`, `@gh-pr-view`, `@gh-pr-review`, `@gh-pr-close` |
