# Notion task board

Sync tasks between an **existing** Notion database and local **task pairs** ([issue #2](https://github.com/gardusig/shuttle-cli/issues/2)).

Local repo is the source of truth. Shuttle does not create databases, views, or formulas.

Naming matches **`shuttle drive`**: **ingest** = into local; **deploy** = out to Notion; **sync** = ingest then deploy.

## Layout

Task root (`notion.task_root`) holds **`metadata/`** and **`body/`** (typically a private directory). The **manifest** (`tasks.pairs.json`) is committed in this repo at `config/notion/tasks.pairs.json` — set `notion.pairs_file` accordingly.

| Path | Role |
| --- | --- |
| `tasks.pairs.json` | Manifest: `{ "metadata_filepath", "body_filepath" }` per task |
| `metadata/**/*.yaml` | **`name`** (unique Notion title) + cadence fields |
| `body/**/*.md` | SOP only — `## Steps`, `## Done when` (cadence lives in metadata) |

**`name`** in metadata yaml is the Notion **title** (unique). The manifest is path pairs only.

## Configuration

`config/config.yaml`:

```yaml
notion:
  database_id: your-notion-database-id
  task_root: ~/git-local/private/configured/notion/tasks
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
shuttle notion pairs build         # scan metadata/ + body/ → tasks.pairs.json
shuttle notion ingest              # Notion → local pairs
shuttle notion deploy --yes        # local pairs → Notion (archives board first by default)
shuttle notion sync --yes          # ingest, then deploy
shuttle notion cleanup --yes       # archive all pages in database
```

Hidden legacy: `download` / `upload`, and older `export` / `import`.

### Deploy

1. Archive all active pages in the database (unless `--no-cleanup`)
2. Upload each manifest entry; skip rows with `enabled: false` in metadata yaml

### Ingest

1. Match board pages by metadata **`name`**
2. Update existing pairs; create `metadata/misc/{slug}.yaml` + body for new titles
3. **`last_done`:** Notion wins on ingest

## Child issues

| Issue | Scope |
| --- | --- |
| [#20](https://github.com/gardusig/shuttle-cli/issues/20) | Ingest (board → pairs) |
| [#21](https://github.com/gardusig/shuttle-cli/issues/21) | Deploy (pairs → board) |
| [#22](https://github.com/gardusig/shuttle-cli/issues/22) | Cleanup (archive all pages) |
| [#23](https://github.com/gardusig/shuttle-cli/issues/23) | Auth, property mapping, automation |

## Task file format

**Metadata** (`metadata/clean/kitchen.yaml`):

```yaml
name: "🍳 kitchen"
priority: 3
tag: hygiene
frequency: weeks
interval: 2
last_done: "2026-06-10"
enabled: true
```

**Body** (`body/clean/kitchen.md`): `## Steps` → `## Done when` only (cadence + title in metadata).

**Manifest** entry:

```json
{
  "metadata_filepath": "metadata/clean/kitchen.yaml",
  "body_filepath": "body/clean/kitchen.md"
}
```
