---
name: read-pr-list-list-view-hub
description: >-
  Read-only: PR list/view narrative hub (no duplicate gh fences). Parent read-pr-list.
---
# PR list / view hub

**Normative command shapes** live in [`read-pr-list`](./SKILL.md) (deprecated redirect). **PR mutations** live in [`read-shuttle-gh-pr-commands`](../../shuttle/gh/pr-commands/SKILL.md).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

