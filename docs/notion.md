# Notion task board

Sync tasks between an **existing** Notion database and local markdown files ([issue #2](https://github.com/gardusig/shuttle-cli/issues/2)).

Local repo is the source of truth. Shuttle does not create databases, views, or formulas.

Naming matches **`shuttle drive`**: **ingest** = into local; **deploy** = out to Notion; **sync** = ingest then deploy.

## Configuration

`config/config.yaml`:

```yaml
notion:
  database_id: your-notion-database-id
  task_directory: data/tasks
  cleanup_before_deploy: false
  properties:
    title: Name
    status: Status
    priority: Priority
    tags: Tags
    id: ID
    created: Created
    updated: Updated
```

**Credentials:** set `NOTION_TOKEN` in the environment (integration token from Notion). Never commit tokens to config.

Older keys `cleanup_before_upload` and `cleanup_before_import` are still read as aliases for `cleanup_before_deploy`.

## Commands

```bash
export NOTION_TOKEN=secret_...
shuttle notion ingest              # Notion → data/tasks/*.md
shuttle notion deploy --yes        # data/tasks → Notion (optional --cleanup)
shuttle notion sync                # ingest, then deploy
shuttle notion cleanup --yes       # archive all pages in database
```

Hidden legacy: `download` / `upload`, and older `export` / `import`.

API implementation is in progress — commands validate config/token then call stubs until child issues land.

## Child issues

| Issue | Scope |
| --- | --- |
| [#20](https://github.com/gardusig/shuttle-cli/issues/20) | Ingest (board → markdown) |
| [#21](https://github.com/gardusig/shuttle-cli/issues/21) | Deploy (markdown → board) |
| [#22](https://github.com/gardusig/shuttle-cli/issues/22) | Cleanup (archive all pages) |
| [#23](https://github.com/gardusig/shuttle-cli/issues/23) | Auth, property mapping, automation |

## Task file format

One file per task: `data/tasks/{id}.md` with YAML frontmatter (`id`, `title`, `status`, `priority`, `tags`, `created`, `updated`) and markdown sections (`# Description`, `# Notes`, `# Checklist`).

See the epic body on GitHub for the full template.
