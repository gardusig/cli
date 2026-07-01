# Repository intelligence skills (roadmap)

Planned public skills for backlog analysis and repo maturity — tracked on GitHub, implemented in separate PRs **after** [PR #58](https://github.com/gardusig/cursor-skills/pull/58) merges.

## Epic

- [#56 — Build Repository Intelligence Skill Catalog](https://github.com/gardusig/cursor-skills/issues/56)

## Child issues

| Issue | Skill | Role |
| --- | --- | --- |
| [#64](https://github.com/gardusig/cursor-skills/issues/64) | `@cursor-repo-prioritize` | Total backlog ordering |
| [#65](https://github.com/gardusig/cursor-skills/issues/65) | `@cursor-repo-dependencies` | Issue dependency graph |
| [#66](https://github.com/gardusig/cursor-skills/issues/66) | `@cursor-repo-roadmap` | Execution phase generator |
| [#67](https://github.com/gardusig/cursor-skills/issues/67) | `@cursor-repo-duplicates` | Overlap detection → `@gh-issue` |
| [#68](https://github.com/gardusig/cursor-skills/issues/68) | `@cursor-repo-completeness` | Domain maturity auditor |
| [#69](https://github.com/gardusig/cursor-skills/issues/69) | `@cursor-repo-catalog-gaps` | Missing topic detection |

## Layout (when implemented)

```
skills/cursor/repo/
  prioritize/SKILL.md
  dependencies/SKILL.md
  …
```

Canonical plan: [`.cursor/plans/cursor-skills.plan.md`](../../.cursor/plans/cursor-skills.plan.md)
