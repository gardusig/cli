---
name: read-pr-content-pr-orchestration
description: >-
  Read-only: @gh-pr orchestration prose. Parent read-pr-content.
---
# PR orchestration (`@gh-pr`)

**Fixed order:** **`read-pr-preflight-qa`** (includes **`read-pr-branch-context`** branch gate) → **`read-pr-prevalidate`** (discover → install → evaluate → **prevalidate_pr** gate) → optional **`@gh-pr-review`** → list matching open PRs / resolve vars (**`read-shuttle-gh-pr-read`**) → **write gate** kind **disambiguate_pr** → resolve `PR_NUM` → **`read-pr-description`** (full: §5 templates, §6 delta, **§6.5–6.6** issue linking + hint scan, **§7** title/body + triple pass) → **write gate** before **`read-shuttle-gh-pr-commands`** → optional **`shuttle gh pr view --json closingIssuesReferences`** when confirmed in that gate.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

