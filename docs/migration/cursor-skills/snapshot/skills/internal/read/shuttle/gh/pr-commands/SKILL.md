---
name: read-shuttle-gh-pr-commands
description: >-
  Read-only: shuttle gh pr write command shapes. Parent read-shuttle-gh.
---
# Internal: shuttle gh PR write (`read-shuttle-gh-pr-commands`)

**Read-only library.** PR mutations via **`shuttle gh`** with **`--yes`** after **Proceed**.

Parent: [`read-shuttle-gh`](../SKILL.md)

## Create

```bash
shuttle gh pr create --title "…" --body-file /path/to/body.md --yes
```

## Edit

```bash
shuttle gh pr edit <N> --body-file /path/to/body.md --yes
```

## Close

```bash
shuttle gh pr close <N> --yes
```

## Merge

```bash
shuttle gh pr merge <N> --merge-method squash --yes
```

## See also

- [`write-pr-commands`](../../../../write/pr/commands/SKILL.md) — legacy (deprecated)
