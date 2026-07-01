---
name: read-docs-reference-wiki-reference-scaffold
description: >-
  Read-only: legacy REFERENCE/wiki page scaffold. Parent read-docs-reference.
---
# Skills reference

Complete catalog of **every** skill in this repository: **public** skills first (user-invoked under `skills/git/` and `skills/gh/`), then **internal** libraries (`skills/<domain>/`). Invocation: `/flattened-name` or `@flattened-name` (path under `skills/` with `/` → `-`, e.g. `skills/gh/pr/SKILL.md` → **`gh-pr`**).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Documentation set (`docs/`)

**Preferred (wiki):** [README.md](README.md), [USER_GUIDE.md](USER_GUIDE.md), **`reference/**`** — scaffold **manual / agent-led** from **`read-docs-reference`** child skills (**`reference-readme-scaffold`**, **`docs-hub-scaffold`**, …) **confirm-first**. **Legacy:** this monolithic **[REFERENCE.md](REFERENCE.md)**; optional **[GRAPHS.md](GRAPHS.md)**. Templates stay in **`skills/internal/read/workflow/doc-*`**.

| Path | Role |
| --- | --- |
| [README.md](README.md) | Doc hub index (wiki layout) |
| [reference/README.md](reference/README.md) | Reference wiki start page |
| [REFERENCE.md](REFERENCE.md) | This file — legacy full catalog |
| [USER_GUIDE.md](USER_GUIDE.md) | Install, prerequisites, workflows |
| [GRAPHS.md](GRAPHS.md) | Optional legacy diagram file |

---

## Folder and file index

Hub **READMEs** (subtree scope and **Related** links)—use with **`docs/reference/**`** or small **mermaid** in each **README** when a diagram helps:

- **[`docs/git.md`](../../../../../docs/git.md)**, **[`docs/gh.md`](../../../../../docs/gh.md)**, **[`docs/read.md`](../../../../../docs/read.md)**, **[`docs/write.md`](../../../../../docs/write.md)** — domain wikis (**this** pack)
- **`skills/git/**`**, **`skills/gh/**`**, **`skills/internal/read/**`**, **`skills/internal/write/**`** — normative **`SKILL.md`** per folder
- **[`skills/internal/read/workflow/SKILL.md`](../../../../read/SKILL.md)**, **[`skills/internal/read/issue/SKILL.md`](../../../../read/SKILL.md)** — library root indexes (**`read-safety-structured-qa`**, **`read-safety-skill-safety`** under **`read/git/`**)

**Scaffold sources** — **`skills/internal/read/workflow/doc-index/`** skeleton child skills + diagram scaffolds under **`read-docs-graphs`**, plus other **`read-docs-*`** child **`SKILL.md`** bodies. **`@git-docs`** only aligns **existing** pages **in place**—it does **not** add new **`docs/`** files from scaffolds alone.

| Scaffold role | Skill | Location |
| --- | --- | --- |
| **`docs/README.md`** + **`docs/reference/**`** | [`read-docs-reference`](../SKILL.md) | [`reference-readme-scaffold/SKILL.md`](../reference-readme-scaffold/SKILL.md), [`docs-hub-scaffold/SKILL.md`](../docs-hub-scaffold/SKILL.md) |
| **`docs/REFERENCE.md`** (legacy) | same | [`wiki-reference-scaffold/SKILL.md`](./SKILL.md) |
| **Optional `docs/GRAPHS.md`** | [`read-docs-graphs`](../doc-graphs/SKILL.md) | [`../doc-graphs/legacy-graphs-pack-scaffold/SKILL.md`](../doc-graphs/legacy-graphs-pack-scaffold/SKILL.md) |
| **`docs/USER_GUIDE.md`** | [`read-docs-user-guide`](../doc-user-guide/SKILL.md) | [`../doc-user-guide/user-guide-scaffold/SKILL.md`](../doc-user-guide/user-guide-scaffold/SKILL.md) |
| **Root `README.md`** | [`read-docs-readme-root`](../readme-root/SKILL.md) | skill body + exemplar § |
| **`docs/...` mirror `README.md`** | [`read-docs-readme-tree`](../readme-tree/SKILL.md) | Rules in **`SKILL.md`**; optional examples under [`doc-index/`](../doc-index/) |

---

## Public skills

### Local git (`skills/git/`)

| Invoke | Source | Description |
| --- | --- | --- |
| **`@git-review`** | [`skills/git/review/SKILL.md`](../../../../git/review/SKILL.md) | *Discover → install → evaluate → §8a docs.* |
| **`@git-docs`** | [`skills/git/docs/SKILL.md`](../../../../git/docs/SKILL.md) | *Post-green doc accuracy: existing `.md` in place only; may no-op; Q&A for scope.* |
| **`@git-main`** | [`skills/git/main/SKILL.md`](../../../../git/main/SKILL.md) | *Align to canonical main.* |
| **`@git-pull`** | [`skills/git/pull/SKILL.md`](../../../../git/pull/SKILL.md) | *Fetch + merge main + conflicts playbook.* |
| **`@git-push`** | [`skills/git/push/SKILL.md`](../../../../git/push/SKILL.md) | *Inventory → `@git-commit` if needed → branch gate → push.* |
| **`@git-reset`** | [`skills/git/reset/SKILL.md`](../../../../git/reset/SKILL.md) | *Reset to target ref.* |
| **`@git-start`** | [`skills/git/start/SKILL.md`](../../../../git/start/SKILL.md) | *Dirty-tree gate → @git-main → new branch → optional @git-push.* |

### GitHub (`skills/gh/`)

| Invoke | Source | Description |
| --- | --- | --- |
| **`@gh-pr`** | [`skills/gh/pr/SKILL.md`](../../../../gh/pr/SKILL.md) | *Preflight → prevalidate → description → **`shuttle gh pr create/edit`**.* |
| **`@gh-pr-*`** (list, view, close, review) | [`skills/gh/pr/`](../../../../gh/pr/) | *PR helpers; mutations via **`read-shuttle-gh-pr-commands`**; read via **`read-shuttle-gh-pr-read`**.* |
| **`@gh-issue-*`** | [`skills/gh/issue/`](../../../../gh/issue/) | *Issues + backlog + labels; read **`read-shuttle-gh-issue-read`**; write **`read-shuttle-gh-issue-commands`**.* |

---

## Internal skills

Libraries under `skills/<domain>/`. Flattened names: path with `/` → `-` (e.g. `write/gh/evaluate` → **`write-quality-evaluate`**).

### Confirm policy (`skills/internal/read/workflow/`)

| Invoke | Source | Description |
| --- | --- | --- |
| **`read-safety-structured-qa`** | [`skills/internal/read/workflow/structured-qa/SKILL.md`](../../../../internal/read/safety/structured-qa/SKILL.md) | *AskQuestion / confirm UX.* |
| **`read-safety-skill-safety`** | [`skills/internal/read/workflow/skill-safety/SKILL.md`](../../../../internal/read/safety/skill-safety/SKILL.md) | *What needs confirm.* |

### Internal libraries (verify + docs + `gh`)

| Invoke | Source | Description |
| --- | --- | --- |
| **`read-config-configuration`** | [`../../../../internal/read/config/configuration/SKILL.md`](../../../../internal/read/config/configuration/SKILL.md) | *Resolve format/lint/test commands.* |
| **`read-dependencies-discover`** | [`../../../../internal/read/dependencies/discover/SKILL.md`](../../../../internal/read/dependencies/discover/SKILL.md) | *Scan repo for stacks and gaps.* |
| **`write-quality-documentation`** | [`../../../../internal/write/quality/documentation/SKILL.md`](../../../../internal/write/quality/documentation/SKILL.md) | *Sharpen existing markdown — §8a.* |
| **`read-docs-readme-tree`** | [`../readme-tree/SKILL.md`](../readme-tree/SKILL.md) | *Read-only mirror bootstrap + checklist.* |
| **`write-quality-evaluate`** | [`../../../../internal/write/quality/evaluate/SKILL.md`](../../../../internal/write/quality/evaluate/SKILL.md) | *Run verify matrix.* |
| **`write-dependencies-install`** | [`../../../../internal/write/dependencies/install/SKILL.md`](../../../../internal/write/dependencies/install/SKILL.md) | *Install / build — §3.* |
| **`read-repo-layout`** | [`../repo-layout/SKILL.md`](../repo-layout/SKILL.md) | *Layout rules — read-only.* |
| **`read-shuttle-gh`** | [`../../../../internal/read/shuttle/gh/SKILL.md`](../../../../internal/read/shuttle/gh/SKILL.md) | *`shuttle gh` command map.* |
| **`read-shuttle-git`** | [`../../../../internal/read/shuttle/git/SKILL.md`](../../../../internal/read/shuttle/git/SKILL.md) | *`shuttle git` read helpers.* |
| **`read-repo-forms-json`** | [`../../../../internal/read/repo/forms-json/SKILL.md`](../../../../internal/read/repo/forms-json/SKILL.md) | *Deprecated → **`read-shuttle-gh-repo-read`**.* |
| **`read-pr-description`** | [`../../../../internal/read/pr/description/SKILL.md`](../../../../internal/read/pr/description/SKILL.md) | *PR templates + delta + title/body.* |
| **`read-pr-body-sections`** | [`../../../../internal/read/pr/body-sections/SKILL.md`](../../../../internal/read/pr/body-sections/SKILL.md) | *Static PR body patterns.* |
| **`read-issue-list`** / **`read-issue-view`** / **`read-pr-list`** | *…* | *Deprecated → **`read-shuttle-gh-*`**.* |
| **`write-issue-commands`** / **`write-pr-commands`** | *…* | *Deprecated → **`read-shuttle-gh-*-commands`**.* |
| **`read-docs-graphs`** | [`../doc-graphs/SKILL.md`](../doc-graphs/SKILL.md) | *README mermaid rules + `diagrams/`.* |
| **`read-docs-reference`** | [`../SKILL.md`](../SKILL.md) | *REFERENCE.md template.* |
| **`read-docs-user-guide`** | [`../doc-user-guide/SKILL.md`](../doc-user-guide/SKILL.md) | *USER_GUIDE.md template.* |
| **`read-docs-exemplars`** | [`../doc-exemplars/SKILL.md`](../doc-exemplars/SKILL.md) | *Public markdown patterns + adoption rubric.* |
| **`read-docs-readme-root`** | [`../readme-root/SKILL.md`](../readme-root/SKILL.md) | *Root README template.* |
| *…* | *…* | *`repo-stream`, `merge-conflicts`, `git-diff-summary`, …* |

---

## Pipeline order (verify)

**`@git-review`:** discover-dependencies → install-dependencies → configuration → evaluate → write-quality-documentation (§8a). Diagram: [GRAPHS.md](GRAPHS.md).

---

## See also

- [Skills graphs](GRAPHS.md)
- [User guide](USER_GUIDE.md)
- [.cursor/scripts/install.sh](../../../../../.cursor/scripts/install.sh) — if your pack uses a copy script
