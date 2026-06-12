# Configuration

Config loads from (first match):

1. `$SHUTTLE_CONFIG_DIR` if set
2. Repo `config/` directory (development)
3. `~/.config/shuttle-cli/`

## Files

| File | Purpose |
| --- | --- |
| `config.yaml` | Backup repos, local git-tags path, Notion, Chrome |
| `drives.yaml` | Google / OneDrive / Proton upload targets |

## Notion tasks

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

- `task_directory` — flat folder of `{id}.md` files (local source of truth)
- `database_id` — existing Notion database (shuttle never creates schema)
- **`NOTION_TOKEN`** — integration token in environment only (not in YAML)

## Chrome bookmarks

```yaml
chrome:
  profile: Default
  bookmarks_file: ~/git-local/shuttle-cli/data/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

- `bookmarks_file` — HTML backup for `shuttle chrome bookmarks ingest` / `deploy`
- `downloads_dir` — where ingest waits for Chrome’s downloaded HTML
- `profile` — reserved for future Chrome profile selection

## Backup (local git-tags)

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/shuttle-cli
```

`tags_dir` must be an absolute path or `~`-expanded path on the local machine (typically an iCloud Drive folder on macOS). Tag zips are created and replaced under `git-tags/{repo-name}/`.

## Drives (cloud upload)

```yaml
drives:
  google:
    enabled: true
    root: git-tags
  onedrive:
    enabled: true
    root: git-tags
  proton:
    enabled: true
    root: git-tags
```

`shuttle drive ingest` zips tags into `backup.tags_dir`; `shuttle drive upload` pushes missing files to each enabled provider.

## Environment overrides

| Variable | Purpose |
| --- | --- |
| `SHUTTLE_CONFIG_DIR` | Override config directory |
| `SHUTTLE_GIT_ROOT` | Test override for git repo root |
| `NOTION_TOKEN` | Notion integration token (required for `shuttle notion`) |
| `SHUTTLE_BOOKMARKS_FILE` | Chrome bookmarks backup path |
| `SHUTTLE_DOWNLOADS_DIR` | Chrome ingest downloads folder |

Git commands use the **current** git repository (`cd` into the repo). Multi-repo backup uses explicit paths in `backup.repositories`.
