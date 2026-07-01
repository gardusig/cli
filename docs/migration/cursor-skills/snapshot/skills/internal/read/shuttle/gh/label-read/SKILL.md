---
name: read-shuttle-gh-label-read
description: >-
  Read-only: shuttle gh label list/sync/delete command shapes. Parent read-shuttle-gh.
---
# Internal: shuttle gh label (`read-shuttle-gh-label-read`)

**Read-only library.** Label inventory and mutations via **`shuttle gh`**.

Parent: [`read-shuttle-gh`](../SKILL.md)

## List

```bash
shuttle gh --format json label list
```

## Sync manifest

```bash
shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml --yes
```

Prune orphans:

```bash
shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml --prune-orphans --yes
```

## Delete one label

```bash
shuttle gh label delete "<name>" --yes
```

## See also

- [`read-issue-label-manifest`](../../../issue/label-manifest/SKILL.md)
- [`read-issue-labels-label-decorate`](../../../issue/labels/label-decorate/SKILL.md) — legacy (deprecated)
