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

See [chrome.md](chrome.md) for workflows and pipeline boundary.

```yaml
chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
  snapshots_dir: ~/git-local/private/bookmarks/snapshots
  snapshot_retention: 30
  profiles:
    Work:
      bookmarks_file: ~/git-local/private/bookmarks/bookmarks-work.html
```

- `bookmarks_file` — HTML backup for ingest / merge / deploy
- `downloads_dir` — folder polled for newest HTML export
- `snapshots_dir` — timestamped copies from `cli chrome bookmarks snapshot`
- `snapshot_retention` — max snapshots per profile (0 = unlimited)
- `profile` / `profiles` — multi-profile backup paths (`--profile` on bookmark commands)

## Backup (local git-tags)

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/cli
    - path: ~/git-local/private
      encrypted: true
  replicas:
    - type: cloud
      provider: google
      root: git-tags
    - type: usb
      path: /Volumes/Backup/git-tags
      name: usb-backup
```

- `tags_dir` — local hub for tag zips (typically iCloud on macOS).
- `repositories[].encrypted` — when `true`, ingest uses password-protected `zip -er` instead of plain `git archive`.
- **`BACKUP_ZIP_PASSWORD`** — zip encryption password in environment only (like `NOTION_TOKEN`).
- `replicas` — deploy targets after ingest: `cloud` (google / onedrive / proton) or `usb` (local mount path). When omitted, enabled entries in `drives.yaml` are used as cloud replicas.

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
    enabled: false
    root: git-tags
```

Cloud providers require OAuth access tokens in the environment (never in YAML):

| Provider | Env var | Optional `auth.yaml` key |
| --- | --- | --- |
| Google Drive | `GOOGLE_DRIVE_TOKEN` | `auth.google_drive.token_file` |
| OneDrive | `ONEDRIVE_TOKEN` | `auth.onedrive.token_file` |

Proton Drive is disabled by default — no stable public upload API (see `docs/drive.md#proton-drive`).

`cli drive ingest` zips tags into `backup.tags_dir`; `cli drive upload` / `deploy` / `sync` push missing files to replicas (append-only). `cli drive download` restores missing remote zips locally.

## Environment overrides

| Variable | Purpose |
| --- | --- |
| `CLI_CONFIG_DIR` | Override config directory |
| `CLI_GIT_ROOT` | Test override for git repo root |
| `NOTION_TOKEN` | Notion integration token (required for `cli notion`) |
| `BACKUP_ZIP_PASSWORD` | Zip password for `encrypted: true` backup repositories |
| `GOOGLE_DRIVE_TOKEN` | Google Drive OAuth access token for `cli drive upload` / `download` |
| `ONEDRIVE_TOKEN` | OneDrive OAuth access token for `cli drive upload` / `download` |
| `CLI_BOOKMARKS_FILE` | Chrome bookmarks backup path |
| `CLI_DOWNLOADS_DIR` | Chrome ingest downloads folder |

Git commands use the **current** git repository (`cd` into the repo). Multi-repo backup uses explicit paths in `backup.repositories`.
