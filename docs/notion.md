# Notion task board

Sync tasks between an **existing** Notion database and local **header/body pairs** ([issue #2](https://github.com/gardusig/cli/issues/2)).

Local repo is the source of truth. Cli does not create databases, views, or formulas — see [notion/board-ui.md](./notion/board-ui.md) and [notion/properties/](./notion/properties/README.md) for one-time board setup.

Naming matches **`cli drive`**: **ingest** = into local; **deploy** = out to Notion; **sync** = ingest then deploy.

## Layout

Task root (`notion.task_root`) holds **`header/`** and **`body/`** (typically a private directory). The **manifest** (`tasks.pairs.json`) and **pair templates** live in this repo under `config/notion/` — set `notion.pairs_file` accordingly.

| Path | Role |
| --- | --- |
| `config/notion/tasks.pairs.json` | Manifest: `{ "header_filepath", "body_filepath" }` per task |
| `config/notion/templates/` | Header/body scaffolds when adding rows |
| `header/**/*.yaml` (under `task_root`) | **`name`** (unique Notion title) + cadence fields |
| `body/**/*.md` (under `task_root`) | SOP only — `## Steps`, `## Done when` (cadence lives in header yaml) |

**`name`** in header yaml is the Notion **title** (unique). The manifest is path pairs only.

Full pair contract: [notion/task-pairs.md](./notion/task-pairs.md).

## Configuration

`config/config.yaml`:

```yaml
notion:
  database_id: your-notion-database-id
  task_root: ~/git-local/private/configured/tasks
  pairs_file: config/notion/tasks.pairs.json
  cleanup_before_deploy: true
  properties:
    title: Name
    priority: Priority
    tag: Tag
    frequency: Frequency
    interval: Interval
    last_done: "Last done"
    forced_status: "Forced status"
```

**Credentials:** set `NOTION_TOKEN` in the environment (integration token from Notion). Never commit tokens to config.

Older keys `task_directory`, `cleanup_before_upload`, and `cleanup_before_import` are still read as aliases.

## Commands

```bash
export NOTION_TOKEN=secret_...
cli notion pairs build         # scan header/ + body/ → tasks.pairs.json
cli notion pairs status        # enabled vs disabled (paused) before deploy
cli notion ingest              # Notion → local pairs
cli notion deploy --yes        # local pairs → Notion (archives board first by default)
cli notion sync --yes          # ingest, then deploy
cli notion cleanup --yes       # archive all pages in database
```

Hidden legacy: `download` / `upload`, and older `export` / `import`.

### Deploy

1. Archive all active pages in the database (unless `--no-cleanup`)
2. Upload each manifest entry; skip rows with `enabled: false` in header yaml

### Ingest

1. Match board pages by header **`name`**
2. Update existing pairs; create `header/misc/{slug}.yaml` + body for new titles
3. **`last_done`:** Notion wins on ingest

## Child issues

| Issue | Scope |
| --- | --- |
| [#20](https://github.com/gardusig/cli/issues/20) | Ingest (board → pairs) |
| [#21](https://github.com/gardusig/cli/issues/21) | Deploy (pairs → board) |
| [#22](https://github.com/gardusig/cli/issues/22) | Cleanup (archive all pages) |
| [#23](https://github.com/gardusig/cli/issues/23) | Auth, property mapping, automation |

## Task file format

**Header** (`header/clean/kitchen.yaml`):

```yaml
name: "🍳 kitchen"
priority: 3
tag: hygiene
frequency: weeks
interval: 2
last_done: "2026-06-10"
enabled: true
```

**Body** (`body/clean/kitchen.md`): `## Steps` → `## Done when` only (cadence + title in header yaml).

**Manifest** entry:

```json
{
  "header_filepath": "header/clean/kitchen.yaml",
  "body_filepath": "body/clean/kitchen.md"
}
```

## Board setup (manual)

1. Create Notion database columns per [notion/properties/](./notion/properties/README.md)
2. Paste formulas from property docs
3. Configure board view per [notion/board-ui.md](./notion/board-ui.md)
