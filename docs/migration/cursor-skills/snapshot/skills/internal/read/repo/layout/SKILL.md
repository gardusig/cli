---
name: read-repo-layout
description: >-
  Read-only: domain-driven skills/, docs/README.md + optional docs/ mirror (this pack), diagram examples under
  skills/internal/read/workflow/doc-graphs/diagrams/*/SKILL.md, minimal root README. Consumed by @git-docs (read-only alignment); not @git-review.
---
# Internal: Repo layout (domain-driven)

**Read-only.** Canonical **shape** for repositories that use this skill pack: **`skills/`** (workflows), **`docs/README.md`** + optional **`docs/...`** beside **`skills/`** (per-folder **`README.md`** and workflow markdown), **`skills/internal/read/workflow/doc-graphs/diagrams/*/SKILL.md`** (optional mermaid examples), and a **minimal** root **`README.md`**. **Does not** run commands or verify—**[`@git-docs`](../../../git/docs/SKILL.md)** aligns **existing** markdown to this contract (**in place** only).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

- Serve as the **single** read-only contract for **`skills/`** + documentation hub shape; callers **read** it and **link** here instead of copying prose.

## Do not

- Run commands, create files, or verify—**[`@git-docs`](../../../git/docs/SKILL.md)** applies **in-place** doc alignment only.

---

## 1. Skills (`skills/`)

Treat **`skills/`** as a **single aggregate** of agent workflows, partitioned by **domain** (bounded context):

| Domain | Typical path | Group together |
| --- | --- | --- |
| **GitHub (`gh`)** | `skills/gh/...` | **`pr`**, **`issue/*`** — **`@gh-*`** only; local git lives under **`skills/git/`** |
| **Cross-cutting internal** | `skills/internal/read/<domain>/**`, `skills/internal/write/<domain>/**` | Domain-first internal libraries (issue, pr, repo, workflow, docs, safety, quality, dependencies, etc.). |
| **Public wikis + scaffolds** | **`docs/git.md`**, **`docs/gh.md`**, **`read-docs-graphs`** `diagrams/` … | **Not** invocable skills—**`.md`** only (diagrams use **fenced `mermaid`** inside those files). |

**Rules**

1. **One skill per folder** — each leaf is `.../<name>/SKILL.md` with YAML **`name`** + **`description`** matching the pack’s conventions.
2. **Similar verbs, same parent** — e.g. all `gh-*` public skills live under **`skills/gh/`**, not scattered at `skills/` root.
3. **Public vs library** — user-invoked flows stay shallow (`skills/<domain>/<verb>`); shared libraries and policies live under `skills/internal/read/<domain>` and `skills/internal/write/<domain>`.
4. **Names mirror behavior** — folder names stay short and match the skill `name` prefix (`git-docs` → `skills/git/docs/`).

When **moving** skill folders, update **relative links** in the same change set; **`read-repo-layout`** stays the single source for layout rules.

---

## 2. Narrative wiki + optional mirror under `docs/`

**Mirror:** when you use one, **`docs/<relpath>/README.md`** may sit beside each **`skills/`** directory; parity expectations are a **repo convention**, not an automated pack step—see **`read-docs-readme-tree`** for a short checklist.

**Root `README.md`:** minimal—title, purpose, install pointer, link **`docs/README.md`** (**`read-docs-readme-root`**).

**`skills/`:** one **`SKILL.md`** per leaf; with a mirror, avoid duplicate prose in **`skills/**/README.md`**—use **`docs/...`** or **`SKILL.md`** only.

**Policy vs bodies:** “when/how” in **`read-docs-*`**, **`read-pr-content`**, **`read-diff-summary`**, **`read-docs-graphs`**; long checklist/skeleton/scaffold bodies as **sibling `.md`** files next to the owning **`read-*` / `write-*`** library; **`docs/`** wikis stay **short** indexes over **`skills/`**.

**Hub scaffold:** use **`read-docs-reference/docs-hub-scaffold/SKILL.md`** as the baseline for emoji headings, numbered `Contents`, and structural comparison tables in new/reshaped docs hubs.

**Exemplars:** **`read-docs-exemplars`**.

---

## 3. What this is not

- **Not** **`@git-review`** — verify + **light** polish of **existing** paths only.
- **Not** **`write-quality-documentation`** in place of this file — that skill **edits** after green tests; **layout policy** stays here only.

---

## See also

- [`read-docs-wiki`](../doc-wiki/SKILL.md) — how deep **`docs/`** might go elsewhere
- [`read-docs-readme-tree`](../readme-tree/SKILL.md) — mirror bootstrap + optional parity checklist
- [`@git-docs`](../../../git/docs/SKILL.md) — post-green doc accuracy (**existing** files **in place**)
- [`write-quality-documentation`](../../internal/write/quality/documentation/SKILL.md) — §8a polish existing docs after green evaluate
- [`docs/README.md`](../../../../docs/README.md) — documentation hub (**this** pack)

## 4. Naming hygiene

- Avoid nested segments repeating the parent (`foo/foo/`). For this pack, keep issue/PR internals under `skills/internal/read/issue/` and git workflows under `skills/internal/read/workflow/`.
- When moving folders, keep `name:` path-faithful with `read-<full-path-with-dashes>` or `write-<full-path-with-dashes>` for library skills.

## 5. Workspace staging conventions (`.cursor/`)

- Optional GitHub issue draft bodies: **`.cursor/gh/issue/<slug>.md`** (see **`read-shuttle-gh-issue-commands`**).
- `.cursor/gh/issue/` stores issue draft bodies/manifests.
- `.cursor/gh/pr/` stores PR draft fragments.
