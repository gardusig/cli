---
name: read-issue-nesting
description: >-
  Read-only: parent epic + child issue patterns, epic label conventions, and batch create order for
  @gh-issue multi-issue flows. Groups one major description with many smaller tracked issues.
---
# Internal: Issue nesting (`read-issue-nesting`)

**Read-only library.** Shape **epic + children** backlogs: one parent issue carries the narrative; child issues are independently executable with shared **epic** labels.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## When

Use when **`@gh-issue`** handoff includes:

- one **theme** that should stay **one epic** but **many deliverables**;
- refactoring a noisy backlog into a parent + children;
- **`read-issue-dedupe`** multi-intent batch where themes share one epic slug.

## Epic label convention

| Label | On | Purpose |
| --- | --- | --- |
| `epic:<slug>` | parent **and** every child | Groups the family (`epic:pack-cleanup`, `epic:repo-intelligence`, …) |
| `issue-type:epic` | parent only | Filter epics in backlog views |
| `issue-type:child` | each child | Filter executable leaves |

**`<slug>`** — lowercase, hyphens, 2–4 words (`repo-intelligence`, `gh-pr-prevalidate`). Custom per epic is fine; **`@gh-issue-labels`** retires stale `epic:*` labels when manifest drifts.

Reuse existing area/type labels (**`enhancement`**, **`documentation`**, …) via **[`read-issue-labels`](../labels/SKILL.md)** — epic labels are **additive** (may exceed three labels on epic flows; caller notes why in chat).

## Parent body (required sections)

```markdown
## Goal
<one paragraph — why this epic exists>

## Scope
<bullets — what the epic covers>

## Child issues
- [ ] #<n> — <title> (filled after children exist)
- [ ] #<n> — …

## Success criteria
<epic done when children are closed or explicitly deferred>
```

## Child body (required sections)

```markdown
## Parent
- Epic: #<parent-n> — <parent title>
- Label: `epic:<slug>`

## Goal
<single deliverable>

## Scope
…

## Success criteria
…

## Execution
<@skill pointers>
```

## Batch create order (`read-shuttle-gh-issue-commands`)

1. **Create parent** with `--label "epic:<slug>,issue-type:epic,…"`.
2. **Create children** with `--label "epic:<slug>,issue-type:child,…"` and **Parent** section referencing parent **#n**.
3. **Edit parent** — append **Child issues** checklist with real **#numbers** (`shuttle gh issue edit <parent> --body-file … --yes`).

One **Proceed — batch** gate may cover all three steps when summarized in chat.

## Dedupe

Run **`read-issue-dedupe`** **per child theme**, not only on the epic narrative. Parent create is **`safe_to_create`** when no open issue already uses the same epic title.

## Refactor pattern (backlog hygiene)

When consolidating duplicates (e.g. brainstorming issue + epic + overlapping children):

1. Pick **one parent** (or create epic).
2. **Edit** keepers into children; **close as duplicate** superseded issues with link to parent.
3. Apply **`epic:<slug>`** to parent + children via **`shuttle gh issue edit … --add-label … --yes`**.

## See also

- [`read-issue-dedupe`](../dedupe/SKILL.md)
- [`read-issue-labels`](../labels/SKILL.md)
- [`read-shuttle-gh-issue-commands`](../../shuttle/gh/issue-commands/SKILL.md)
- [`@gh-issue`](../../../../gh/issue/SKILL.md)
- [`@gh-issue-labels`](../../../../gh/issue/labels/SKILL.md)
