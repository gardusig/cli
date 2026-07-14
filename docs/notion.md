# Notion task board

Sync tasks between an **existing** Notion database and local **header/body pairs**.

Local repo is the source of truth. Cli does not create databases, views, or formulas — see [notion/board-ui.md](./notion/board-ui.md) and [notion/properties/](./notion/properties/README.md) for one-time board setup.

Naming matches **`cli drive`**: **ingest** = into local; **deploy** = out to Notion; **sync** = ingest then deploy.

## Layout

Task root (`notion.task_root`) holds **`header/`** and **`body/`** (typically a private directory). The **manifest** (`tasks.pairs.json`) path is set via `notion.pairs_file`. Header/body scaffolds ship in **`src/data/notion/templates/`**.

| Path | Role |
| --- | --- |
| `tasks.pairs.json` (or custom path) | Manifest: `{ "header_filepath", "body_filepath" }` per task |
| `src/data/notion/templates/` | Header/body scaffolds when adding rows |
| `header/**/*.yaml` (under `task_root`) | **`name`** (unique Notion title) + cadence fields |
| `body/**/*.md` (under `task_root`) | SOP only — `## Steps`, `## Done when` (cadence lives in header yaml) |

**`name`** in header yaml is the Notion **title** (unique). The manifest is path pairs only.

Full pair contract: [notion/task-pairs.md](./notion/task-pairs.md).

## Configuration

User `config.yaml` (see `cli configure`):

```yaml
notion:
  database_id: your-notion-database-id
  task_root: ~/git-local/private/tasks
  pairs_file: tasks.pairs.json
  link_branch: main
  cleanup_before_deploy: true
  properties:
    title: Name
    priority: Priority
    tag: Tag
    frequency: Frequency
    interval: Interval
    last_done: "Last done"
    forced_status: "Forced status"
    link: link
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
3. Set Notion **`link`** to the GitHub runbook URL from `notion.link_repo` + `body_filepath` (see [properties/link.md](./notion/properties/link.md))

Per-task API failures are reported and the command exits non-zero if any deploy failed (successful pages are kept).

### Ingest

1. Match board pages by header **`name`**
2. Update existing pairs; create `header/misc/{slug}.yaml` + body for new titles
3. **`last_done`:** Notion wins on ingest
4. **`link`:** database repo url written to header yaml (overwrites Notion board value)

## Commands

| Command | Direction |
| --- | --- |
| `cli notion ingest` | Notion board → local pairs |
| `cli notion deploy` | Local pairs → Notion board |
| `cli notion cleanup` | Archive all board pages |
| `cli notion sync` | Ingest then deploy |
| `cli notion pairs build` | Scan header/body → manifest |
| `cli tasks …` | Shortcuts — see [tasks.md](./tasks.md) |

## Task automation

```bash
cli tasks list
cli tasks run notion ingest
cli tasks run notion deploy --yes
cli tasks ingest-pr --source notion --yes   # ingest → pairs build → PR (database repo)
```

See [tasks.md](./tasks.md) for the private task-data workflow.

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
