---
name: read-docs-reference-reference-readme-scaffold
description: >-
  Read-only: root README long-form scaffold. Parent read-docs-reference.
---
# Reference wiki

Deep dives and catalogs. **Diagrams:** use self-contained **`mermaid`** in each page; **color and spine** rules live only in **`read-docs-graphs`** (**`SKILL.md`** + **`diagrams/*/SKILL.md`**)—do not paste authoring appendix tables into published docs.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Contents

| Page | Description |
| --- | --- |
| <e.g. [skills.md](skills.md)> | <Public + internal skill summaries — link to `SKILL.md`> |
| <e.g. [pipelines.md](pipelines.md)> | <Verify / PR / context flows> |

---

## Folder and file index

Link every domain **`README.md`** under **`skills/`** (and other top-level folders) so readers can jump from wiki to subtree owners.

- **[docs/git.md](../../../../../docs/git.md)**, **[docs/gh.md](../../../../../docs/gh.md)**, **[docs/read.md](../../../../../docs/read.md)**, **[docs/write.md](../../../../../docs/write.md)** (domain docs for `skills/`, **this** pack)
- <add per-domain READMEs>

---

## Template sources (internal)

| Role | Skill |
| --- | --- |
| Wiki hub | `read-docs-reference` — child **`SKILL.md`** bodies (e.g. **`wiki-reference-scaffold`**) + repo **`docs/`** |
| User guide | `read-docs-user-guide` |
| Diagram authoring | `read-docs-graphs` |
| Root / folder README | `read-docs-readme-root`, `read-docs-readme-tree` |

---

## Related

- [Documentation index](../SKILL.md)
- [USER_GUIDE.md](../USER_GUIDE.md)
