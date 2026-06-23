# Configuration

Config loads from (first match):

1. `$CLI_CONFIG_DIR` if set
2. Repo `config/` directory (development)
3. `~/.config/cli/`

## Files

| File | Purpose |
| --- | --- |
| `config.yaml` | Backup repos, local git-tags path, Notion, Chrome |
| `drives.yaml` | Google / OneDrive / Proton upload targets |
| `ci/config.yaml` | Docker unit/integration overrides (fixture paths); set via `CLI_CONFIG_DIR` |
| `contest/defaults.yaml` | `cli contest validate` timeout, memory, image defaults |
| `contest/templates/` | Generator and brute scaffolds for competitive programming |

See [`config/README.md`](../config/README.md) for how CI overrides relate to the root files.

## Notion tasks

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

- `task_root` — private folder with `header/` and `body/` (task content)
- `pairs_file` — manifest path; use `config/notion/tasks.pairs.json` in this repo (or a bare filename under `task_root` for tests)
- `header` yaml **`name`** — unique Notion title (required in each yaml)
- `database_id` — existing Notion database (cli never creates schema)
- **`NOTION_TOKEN`** — integration token in environment only (not in YAML)

## Chrome bookmarks

```yaml
chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

- `bookmarks_file` — HTML backup for `cli chrome bookmarks ingest` / `deploy`
- `downloads_dir` — where ingest waits for Chrome’s downloaded HTML
- `profile` — reserved for future Chrome profile selection

## Backup (local git-tags)

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/cli
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

`cli drive ingest` zips tags into `backup.tags_dir`; `cli drive upload` pushes missing files to each enabled provider.

## Environment overrides

| Variable | Purpose |
| --- | --- |
| `CLI_CONFIG_DIR` | Override config directory |
| `CLI_GIT_ROOT` | Test override for git repo root |
| `NOTION_TOKEN` | Notion integration token (required for `cli notion`) |
| `CLI_BOOKMARKS_FILE` | Chrome bookmarks backup path |
| `CLI_DOWNLOADS_DIR` | Chrome ingest downloads folder |

Git commands use the **current** git repository (`cd` into the repo). Multi-repo backup uses explicit paths in `backup.repositories`.
