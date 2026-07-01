---
name: read-repo-classification
description: >-
  Read-only: classify repository kind (markdown-first vs code vs multi-service/monorepo vs tooling-heavy) from tree
  skim plus optional read-dependencies-discover summary. Recommendations for doc stance only—no writes. Callers
  may use output to scope issue-shaping chat.
---
# Internal: Repository classification (`read-repo-classification`)

**Read-only library.** Produces a **short label**, **evidence bullets**, and **suggested documentation stance** for the open workspace. **Does not** replace **[`read-dependencies-discover`](../discover-dependencies/SKILL.md)** (toolchains, CI, check commands)—combine a **quick tree skim** with that skill’s summary when available.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Do

1. **Skim** repo root and one level down: **`skills/`**, **`docs/`**, **`src/`**, **`apps/`**, **`packages/`**, **`services/`**, `package.json`, lockfiles, CI config, dominant extensions (`.md` vs `.ts`/`.go`/`.py`).
2. **Optionally** ingest **`read-dependencies-discover`** output: languages/stacks, “docs-only” vs real code checks, monorepo/workspace signals.
3. **Emit for chat** (recommendations only):
   - **Primary label** — one of: **`markdown-docs-first`**, **`code-app-or-library`**, **`multi-service-monorepo`**, **`scripts-tooling-heavy`**, or **`mixed`** (state why).
   - **Evidence** — **2–5** bullets (paths, artifacts, CI).
   - **Suggested doc stance** — e.g. minimal **`docs/README.md`** only vs full **[`read-docs-wiki`](../doc-wiki/SKILL.md)** **`coding`** profile vs **`skill-pack`** / **`knowledge`**; whether **`docs/api/`** is plausible (see **`read-docs-wiki`** §3).

## Kind reference (signals)

| Kind | Typical signals |
| --- | --- |
| **Markdown / docs-first** | Mostly **`.md`**; **`skills/**/SKILL.md`** trees; little or no app **`src/`**; no or trivial build/test stack. |
| **Code present** | Lockfiles, **`src/`** / language-specific roots, CI running tests/build; single product or library. |
| **Multi-service / monorepo** | **`services/`**, **`apps/*`**, **`packages/*`**, **`pnpm-workspace.yaml`**, **`go.work`**, multiple deployables. |
| **Tooling-heavy** | **`tools/`**, Make/Task **`justfile`**, small CLIs, automation entrypoints; docs may still matter but the codebase is automation-centric. |

**Modifiers:** A repo can be **`markdown-docs-first` + `scripts-tooling-heavy`** (e.g. skill pack with **`.cursor/scripts/install.sh`**). Prefer the label that best answers “what is the main artifact?”

## Do not

- Run commands, write files, or mutate git from this skill.
- Treat classification as **authoritative** without user confirmation when it drives large doc or structural changes.
- Duplicate **`read-docs-wiki`** profile tables—**link** there for path-level detail.

## See also

- [`read-dependencies-discover`](../discover-dependencies/SKILL.md)
- [`read-docs-wiki`](../doc-wiki/SKILL.md)
- [`read-repo-layout`](../repo-layout/SKILL.md)
- [`write-quality-documentation`](../../write/quality/documentation/SKILL.md) — in-place updates on **existing** **`.md`** only when a quality pass runs
