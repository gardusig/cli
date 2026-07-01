---
name: read-repo-project-structure-eval
description: >-
  Read-only: one-pass repository structure/readiness evaluation that combines repo classification and optional dependency discovery into
  pillar status, posture, prioritized themes, and tracking recommendation. No installs, tests, or GitHub mutations.
---
# Internal: Project structure evaluation (`read-repo-project-structure-eval`)

**Read-only library.** Produces a concise repository posture snapshot for issue shaping and repo health chat:

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Consumers

- **`@git-start`**, **`@gh-issue`**, **`@gh-issue-backlog`**, **`@gh-issue-review`**
## Non-goals

- No dependency installs
- No format/lint/test execution
- No git mutation
- No `gh` mutation
- No file writes

## Procedure

1. **Collect context**
   - Skim root and first-level structure (`skills/`, `docs/`, `src/`, `apps/`, `packages/`, `services/`, lockfiles, CI files).
   - Reuse existing summary from `read-repo-classification`.
   - Optionally layer in dependency/CI/check-command clues from `read-dependencies-discover`.
2. **Select primary kind**
   - Use one primary kind from `repo-classification` and mention relevant modifiers.
3. **Evaluate pillars**
   - Score each pillar as `Have`, `Missing`, `Unknown`, or `N/A`.
   - Include one short rationale per pillar.
4. **Determine posture**
   - `good-shape`: mostly `Have`, few/no critical `Missing`.
   - `needs-foundation`: several critical `Missing`.
   - `mixed`: meaningful strengths with material gaps.
5. **Return impact-ordered themes**
   - 0-5 themes, highest impact first.
6. **Return tracking recommendation**
   - Keep refining in chat when scope is uncertain.
   - Open GitHub issue(s) when implementation-ready actions are clear.

## Pillars and status rules

| Pillar | What to look for | Status guidance |
| --- | --- | --- |
| Repository shape clarity | Clear top-level structure and ownership hints (`README`, domain docs, folder conventions) | `Have` when navigation is clear; `Missing` when structure is opaque |
| Workflow contracts | Public/internal skill boundaries and orchestration docs are coherent | `Have` when contracts are consistent; `Missing` for contradictory guidance |
| Verification surface | Meaningful evaluation path exists for repo kind (`N/A` for checks that do not apply) | For markdown-first repos, code-only CI gates can be `N/A` |
| Documentation integrity | Core docs/indexes and links align with current tree/contracts | `Missing` when docs drift; `Unknown` if evidence is incomplete |
| Safety and mutation controls | Confirm-first policies for risky operations are explicit | `Missing` if high-risk actions can occur without explicit confirmation |

## N/A vs Missing guidance

- Use **`N/A`** when a pillar genuinely does not apply to the repository kind.
  - Example: markdown-first pack without runtime services => service-deploy readiness is `N/A`.
- Use **`Missing`** when the pillar should apply but required evidence is absent.
  - Example: repo has executable code and CI references tests, but no clear local verification path.
- Use **`Unknown`** when evidence is insufficient and additional inspection is required.

## Output contract (chat shape)

1. **Repo kind**: `<primary-kind>` (+ modifiers)
2. **Evidence**: 2-5 bullets
3. **Pillar table**: `Pillar | Status | Rationale`
4. **Posture**: `good-shape` | `needs-foundation` | `mixed`
5. **Themes**: 0-5 impact-ordered bullets
6. **Tracking recommendation**: `refine-in-chat` or `open-issue`

## See also

- [`read-repo-classification`](../repo-classification/SKILL.md)
- [`read-dependencies-discover`](../discover-dependencies/SKILL.md)
- [`read-repo-layout`](../repo-layout/SKILL.md)
- [`@gh-issue`](../../../gh/issue/SKILL.md)
- [`@gh-issue-review`](../../../gh/issue/review/SKILL.md)
