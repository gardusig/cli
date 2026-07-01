---
name: read-issue-label-manifest
description: >-
  Read-only: .cursor/gh/labels.manifest.yaml taxonomy and labelize heuristics for @gh-issue-labels.
---
# Internal: Label manifest (`read-issue-label-manifest`)

**Read-only library.** Repo label catalog at **`.cursor/gh/labels.manifest.yaml`**.

## Manifest path

`.cursor/gh/labels.manifest.yaml` in target repo cwd.

## Sync command

```bash
shuttle gh label sync --manifest .cursor/gh/labels.manifest.yaml --yes
```

## Labelize heuristics (AI)

| Signal | Label candidate |
| --- | --- |
| Epic flow | `issue-type:epic`, `issue-type:child`, `epic:<slug>` |
| Bug/fix | `bug` |
| Docs-only | `documentation` |
| Skill pack work | `area:skills` (if in manifest) |

Propose 0–3 labels per issue via [`read-issue-labels`](../labels/SKILL.md); manifest defines allowed names.

## Protected labels

Never delete defaults listed under **`protected:`** in manifest unless user explicitly overrides.

## See also

- [`read-shuttle-gh-label-read`](../../shuttle/gh/label-read/SKILL.md)
- [`@gh-issue-labels`](../../../../gh/issue/labels/SKILL.md)
