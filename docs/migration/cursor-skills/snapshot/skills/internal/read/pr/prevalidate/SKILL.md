---
name: read-pr-prevalidate
description: >-
  Read-only orchestration contract for @gh-pr: discover repo checks from docs/CI, run install + evaluate
  sequence, emit pass/fail checklist before PR draft. Reduces CI back-and-forth after PR open.
---
# Internal: PR pre-validate (`read-pr-prevalidate`)

**Orchestration library** for **`@gh-pr`**. After branch confirmation, **discover** what the repo expects before a PR, **run** the command sequence when applicable, and **gate** PR text / create on a green checklist (or explicit user override).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## When

Run **after** **`read-pr-branch-context`** Proceed and **before** **`read-pr-description`** §5–7, unless the user explicitly skips validation (`SKIP_PR_PREVALIDATE=true` or **Proceed — skip checks** at the validation gate).

## Fixed order

1. **Discover** — **[`read-dependencies-discover`](../../dependencies/discover/SKILL.md)** (README, `docs/`, CI, config signals).
2. **Resolve commands** — **[`read-config-configuration`](../../config/configuration/SKILL.md)** from discovery output.
3. **Map gaps** — from discover Batch B; if install required, run **[`write-dependencies-install`](../../../write/dependencies/install/SKILL.md)** (destructive steps per **`read-safety-structured-qa`**).
4. **Evaluate** — **[`write-quality-evaluate`](../../../write/quality/evaluate/SKILL.md)** (umbrella → format → lint → test → coverage per stack).
5. **Checklist** — emit a table in chat:

| Step | Command (or skip reason) | Result |
| --- | --- | --- |
| Discover | … | stacks: … |
| Install | … | pass / skip / fail |
| Umbrella | … | pass / skip / fail |
| Format | … | pass / skip / fail |
| Lint | … | pass / skip / fail |
| Test | … | pass / skip / fail |
| Coverage | … | pass / skip / N/A |

6. **Write gate** — kind **prevalidate_pr**:
   - **Abort**
   - **Fix failures first** (stop; user fixes tree)
   - **Proceed — checks green** (continue to PR lookup / draft)
   - **Proceed — skip checks** (only when user accepts risk; record in chat)

**Docs-only / skill-pack repos:** discovery may resolve to `./.cursor/scripts/run.sh` or documented pack checks — run them when present.

## Skill-pack default (this repository)

When **`PR_TARGET_REPO`** is **`gardusig/cursor-skills`** (or local tree matches pack layout):

- Prefer **`./.cursor/scripts/run.sh`** when `public-skills.txt` exists.
- Treat green **`run.sh`** as satisfying format/lint/test gates for PR prevalidate.

## Do not

- Open or edit the PR before the **prevalidate_pr** gate resolves (unless user chose **skip checks**).
- Hide failing command output — paste stderr tail (last ~30 lines) per failed step.

## See also

- [`read-dependencies-discover`](../../dependencies/discover/SKILL.md)
- [`write-quality-evaluate`](../../../write/quality/evaluate/SKILL.md)
- [`read-pr-branch-context`](../branch-context/SKILL.md)
- [`@gh-pr`](../../../../gh/pr/SKILL.md)
