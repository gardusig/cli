---
name: read-docs-user-guide-user-guide-scaffold
description: >-
  Read-only: legacy USER_GUIDE scaffold. Parent read-docs-user-guide.
---
---
template_for: docs/USER_GUIDE.md
source_skill: read-docs-user-guide
instructions: >-
  Copy into docs/USER_GUIDE.md. Replace skill names and paths with your pack. Link install to root README.
---

# User guide

**Purpose:** **install from scratch**, **prerequisites**, **workflows**, **per-repo storage**, **troubleshooting**. Use **raw Terminal commands** (especially on **macOS**). **README-only repos:** fold this into **root `README.md`**; catalogs live in **`docs/README.md`** plus **`docs/git.md`**, **`docs/gh.md`**, **`docs/read.md`**, **`docs/write.md`**, … (**this** pack) or optional **`docs/`** mirror. **Legacy:** deep catalogs in **`docs/reference/**`** or **[REFERENCE.md](REFERENCE.md)**; hub index **`docs/README.md`** if present.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Prerequisites (macOS)

Run in **Terminal** (replace versions with what your project needs).

```bash
# Xcode CLI tools (if prompted)
xcode-select --install

# Homebrew (if missing) — see https://brew.sh
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Example toolchains (adapt)
brew install git
brew install gh && gh auth login
# brew install node@22   # if your pack needs Node
```

**Cursor:** install the editor from vendor instructions; restart after adding skills. **Skills install:** from repo root, `./.cursor/scripts/install.sh` (or your pack’s script)—see root **README**.

---

## Diagrams

Prefer **small `mermaid` blocks** in **folder `README.md`** / **root `README.md`** (README-only), or in **`docs/reference/**`** (legacy). **Color / spine rules:** **`read-docs-graphs`** **`SKILL.md`** + **`diagrams/`** child skills—optional legacy **`docs/GRAPHS.md`**, not default. Optional PNG export: **`diagrams/diagrams-index/SKILL.md`** in that library.

---

## Workflows

Open a **target git repo** in Cursor. Invoke with `/skill-name` or `@skill-name`.

> **This pack (cursor-skills):** GitHub workflows use **`@gh-*`** skills + **[shuttle-cli](https://github.com/gardusig/shuttle-cli)** (`shuttle gh`, `shuttle git`). No public **`@git-*`** skills. Tables below marked *other repos* apply when your fork of the pack still ships git orchestrators.

| Goal | Skills (this pack) |
| --- | --- |
| Discovery → issues | chat/planning → `@gh-issue` |
| Backlog → execute | `@gh-issue-backlog` / `@gh-issue-next` → `@gh-issue-execute` |
| Pull request | `@gh-pr` (prevalidate + `shuttle gh pr create/edit`) |
| PR review | `@gh-pr-review` or `@gh-pr-view` |
| Merge | GitHub UI after merge-ready verdict |

| Goal | Skills (*other repos* with full git pack) |
| --- | --- |
| Issue → implement → PR | `@gh-issue-pick` / `@gh-issue-view` → `@git-start` → `@gh-pr` |
| Verify (no push) | `@git-review` |
| Commit + push | `@git-push` |
| Doc polish (existing paths) | `write-quality-documentation` after green verify |

---

## Documentation workflow

| Situation | Skill | Notes |
| --- | --- | --- |
| Greenfield or missing mirror / large `docs/` reshuffle | Normal change set | Add or move **`docs/`** paths in git like any other source; use **`read-docs-readme-tree`** + **`read-repo-layout`** as guides; **`read-safety-skill-safety`** when the diff is huge. |
| After code changes, before PR | `@gh-pr` prevalidate or `./.cursor/scripts/run.sh` | **`@gh-pr`** runs discover/evaluate when applicable; doc-only tweaks via **`write-quality-documentation`** on existing **`.md`**. |
| After tests pass (verify pipeline) | `write-quality-documentation` | Light polish on **existing** paths. |

Do **not** use a verify skill alone to **reshape** the whole doc tree for big moves — do that as explicit file edits with the usual review and safety confirms.

---

## Per-repo storage (`<project>/.cursor/`)

Optional **`.cursor/`** snippets — copy subtrees from this pack’s **`docs/`** (and diagram scaffolds under **`skills/internal/read/workflow/doc-graphs/diagrams/`**) (see root **`README.md`** and **`docs/README.md`**).

---

## Troubleshooting

| Issue | What to try |
| --- | --- |
| Skill not listed | Re-run your install script; restart Cursor |
| Stack not detected | README + CI config at repo root |
| Checks fail | Install toolchains; re-run `./.cursor/scripts/run.sh` or `@gh-pr` prevalidate |
| `gh` CLI missing | Install GitHub CLI and `gh auth login` |

---

## See also

- **[Skills reference](REFERENCE.md)**
- **[Skills graphs](GRAPHS.md)**
- **[Root README](../README.md)**
