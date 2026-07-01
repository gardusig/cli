---
name: read-issue-description-issue-context
description: >-
  Read-only: optional local scratch notes that reference a GitHub issue (#n, URL). Parent read-issue-description.
  Not a substitute for issue bodies on GitHub.
---
# Issue-linked local notes

Optional convention when the user wants a **local** file beside an issue workflow (not stored on GitHub).

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Suggested layout

- Draft issue bodies for **`@gh-issue`**: **`.cursor/gh/issue/<slug>.md`** (see **`read-shuttle-gh-issue-commands`**).
- Optional delivery checklist after **`@gh-issue-view`**: short markdown in chat or a user-chosen path under **`.cursor/gh/`** with **#n**, title, acceptance bullets, and links to **`@git-start`** / **`@gh-pr`**.

## Do not

- Treat this file as a second issue body on GitHub.
- Require a separate scratch-hub markdown file outside **`.cursor/gh/`** for pack workflows.

## See also

- [`read-issue-view`](../../issue-view/SKILL.md)
- [`@gh-issue-view`](../../../../gh/issue/view/SKILL.md)
- [`@gh-issue`](../../../../gh/issue/SKILL.md)
