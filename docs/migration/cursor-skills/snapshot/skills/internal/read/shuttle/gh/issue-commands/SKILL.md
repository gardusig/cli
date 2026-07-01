---
name: read-shuttle-gh-issue-commands
description: >-
  Read-only: shuttle gh issue write command shapes (create/edit/close/delete/comment/batch).
  Parent read-shuttle-gh. Replaces write-issue-commands gh fences.
---
# Internal: shuttle gh issue write (`read-shuttle-gh-issue-commands`)

**Read-only library.** Issue **mutations** via **`shuttle gh`** — append **`--yes`** after Cursor **Proceed**.

Parent: [`read-shuttle-gh`](../SKILL.md)

## Double-gate

Cursor **AskQuestion Proceed** → shuttle command with **`--yes`**.

## Create

```bash
shuttle gh issue create --title "…" --body-file /path/to/body.md --label bug --yes
```

## Edit

```bash
shuttle gh issue edit <N> --title "New title" --yes
shuttle gh issue edit <N> --body-file /path/to/body.md --yes
shuttle gh issue edit <N> --add-label bug --remove-label triage --yes
```

## Close

```bash
shuttle gh issue close <N> --comment "…" --yes
```

## Delete

```bash
shuttle gh issue delete <N> --yes
```

## Comment

```bash
shuttle gh issue comment <N> --body "…" --yes
```

## Batch (epic + children)

Write `batch.yaml` then:

```bash
shuttle gh issue batch --file batch.yaml --yes
```

Batch shape: see [shuttle-cli docs/gh.md](https://github.com/gardusig/shuttle-cli/blob/main/docs/gh.md).

## See also

- [`write-issue-commands`](../../../../write/issue/commands/SKILL.md) — legacy (deprecated)
