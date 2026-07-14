# Task pairs (header + body)

Parallel-path pairs joined by `notion.pairs_file` (typically `tasks.pairs.json` under your private `notion.task_root`). Task **files** live in that task root; templates ship in `src/data/notion/templates/`.

## Pair contract

| Folder | Contents |
| --- | --- |
| **header/** | `*.yaml` — **`name`** (unique Notion title) + cadence fields |
| **body/** | `*.md` only — `## Steps` + `## Done when` |

**Join key:** `header/<path>.yaml` ↔ `body/<path>.md` (same relative stem)

## Manifest

```json
{
  "header_filepath": "header/clean/kitchen.yaml",
  "body_filepath": "body/clean/kitchen.md"
}
```

Build or refresh:

```bash
cli notion pairs build
```

## Body writing

- Template: [src/data/notion/templates/body.md](../../src/data/notion/templates/body.md) (header: [header.yaml](../../src/data/notion/templates/header.yaml))
- Shape: `## Steps` → `## Done when`
- **No** title or cadence intro in body — `name` + schedule fields live in header yaml
- No links to other files in body prose

## Add a board row

1. Pick a path stem, e.g. `clean/kitchen`.
2. Copy [src/data/notion/templates/header.yaml](../../src/data/notion/templates/header.yaml) → `header/clean/kitchen.yaml` with **`name`** + cadence fields.
3. Copy [src/data/notion/templates/body.md](../../src/data/notion/templates/body.md) → `body/clean/kitchen.md` using the body template.
4. Run `cli notion pairs build`.

## Last done policy

When you finish a task in real life, update **`last_done`** in the matching header yaml. If Notion **Last done** drifts after manual board edits, **Notion wins** on ingest until you reconcile yaml on the next git pass.

**Upstream:** [Notion hub](../notion.md)
