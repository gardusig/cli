---
name: read-docs-mirror-bootstrap
description: >-
  Read-only: bootstrap docs/ mirror pages from README inventory using canonical internal doc libraries.
---
# Internal: docs mirror bootstrap

**Read-only.** Use this when creating a docs mirror for the first time or after a large layout change. This is not part of `@git-review` and does not replace in-place updates from `@git-docs`.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Inputs

- Repository root.
- Scope (`skills/` subtree only, or full repository).

## Steps

1. Enumerate candidate `README.md` files in the chosen scope.
2. Decide which paths should have a docs mirror page.
3. Map each source path to a `docs/<parallel-path>/README.md` target.
4. Draft each target page using canonical doc libraries:
   - [`read-docs-index`](../doc-index/SKILL.md)
   - [`read-docs-explanation`](../doc-explanation/SKILL.md)
   - [`read-docs-table`](../doc-table/SKILL.md) when reference tables are needed
5. Apply wiki/layout constraints from:
   - [`read-repo-layout`](../repo-layout/SKILL.md)
   - [`read-docs-index`](../doc-index/SKILL.md)
6. For diagram-heavy pages, use [`read-docs-graphs`](../doc-graphs/SKILL.md) and child templates.

## Do not

- Treat this as continuous mirror regeneration.
- Replace `@git-docs` or `write-quality-documentation` for routine in-place doc alignment.
