# Skill Link Audit

This file freezes the singleton merge set used by the current refactor.

## Method

- Source set: all `skills/**/SKILL.md`.
- Edge rule: markdown links that resolve to another local `SKILL.md`.
- A skill is a merge candidate only when it has exactly one inbound parent.
- A skill stays independent when it has two or more inbound parents.

## Frozen merge batches

### Batch A (execute now)

- `skills/internal/read/issue/issue-dedupe/issues-orchestration/SKILL.md` -> `skills/internal/read/issue/issue-dedupe/SKILL.md`
- `skills/internal/read/issue/issue-spec/exemplars/calculator-operations/SKILL.md` -> `skills/internal/read/issue/issue-spec/SKILL.md`
- `skills/internal/read/issue/issue-spec/exemplars/issue-router-upgrade/SKILL.md` -> `skills/internal/read/issue/issue-spec/SKILL.md`
- `skills/internal/read/workflow/doc-index/pasteable-explanation/SKILL.md` -> `skills/internal/read/workflow/doc-explanation/SKILL.md`
- `skills/internal/read/workflow/doc-index/pasteable-index/SKILL.md` -> `skills/internal/read/workflow/doc-index/SKILL.md`
- `skills/internal/read/workflow/doc-index/pasteable-table/SKILL.md` -> `skills/internal/read/workflow/doc-table/SKILL.md`

### Batch B (defer)

- `skills/internal/read/workflow/doc-graphs/diagrams/scaffold-*` singleton children under `diagrams-index` (deferred because this would produce one large scaffold file).
- `skills/internal/read/workflow/readme-root/root-readme-scaffold/SKILL.md` (deferred because it is part of legacy readme scaffolding and not required for this pass).

## Carve-outs (keep independent)

- `skills/internal/read/workflow/doc-graphs/diagrams/palette/SKILL.md`
- `skills/internal/read/workflow/doc-graphs/diagrams/examples/SKILL.md`
- `skills/internal/read/workflow/doc-graphs/legacy-graphs-pack-scaffold/SKILL.md`

Reason: `skills/internal/read/workflow/doc-graphs/SKILL.md` explicitly says to keep long palette/examples content in child skills and link to them.

## Multi-parent hold

Any skill linked by 2+ other skills remains independent in this refactor wave.
