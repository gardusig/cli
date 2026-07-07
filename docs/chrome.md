# Chrome browser integrations

**`cli chrome`** owns bookmark file ingest/deploy for Chrome HTML exports. Browser export/import steps stay manual; this repo does not add shell scripts, launchd plists, or workflow YAML.

Parent epic: [issue #24](https://github.com/gardusig/python-cli/issues/24). Legacy bookmarks scripts: [issue #1](https://github.com/gardusig/python-cli/issues/1) (superseded by `cli chrome bookmarks`). [Issue #48](https://github.com/gardusig/python-cli/issues/48) (bookmarks update script) is superseded by `merge` + `snapshot` — no separate update script ships in this repo.

| Phase | Command | What it does |
| --- | --- | --- |
| Ingest | `chrome bookmarks ingest` | Copy newest HTML export into configured backup |
| Deploy | `chrome bookmarks deploy` | Validate backup is ready for manual Chrome import |
| Merge | `chrome bookmarks merge` | Append new URLs from export (dedupe by URL) |
| Snapshot | `chrome bookmarks snapshot` | Timestamped copy under `chrome.snapshots_dir` |

## Manual roundtrip

```bash
# In Chrome: Bookmarks → Bookmark Manager → ⋮ → Export bookmarks
cli chrome bookmarks ingest
cli chrome bookmarks snapshot          # optional safety copy
cli chrome bookmarks merge --dry-run   # optional incremental update
cli chrome bookmarks deploy
# In Chrome: ⋮ → Import bookmarks → select backup file
```

Scheduled or headless export jobs belong in **`gardusig/github-pipelines`**, not this repo.

## Configuration

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

| Env var | Purpose |
| --- | --- |
| `CLI_BOOKMARKS_FILE` | Override backup path (default profile only) |
| `CLI_DOWNLOADS_DIR` | Poll folder for HTML exports |
| `CLI_BOOKMARKS_SOURCE` / `CLI_BOOKMARKS_FIXTURE` | Explicit ingest/merge source (tests/CI) |
| `CLI_SKIP_CHROME_AUTOMATION` | Skip download polling; use newest/fixture file |

## Troubleshooting (#27)

| Situation | What to do |
| --- | --- |
| Export poll times out | Set `CLI_SKIP_CHROME_AUTOMATION=1` and pass `CLI_BOOKMARKS_SOURCE` / place HTML in `CLI_DOWNLOADS_DIR` |
| Wrong backup file | Set `CLI_BOOKMARKS_FILE` or use `--profile` with `chrome.profiles` |
| No snapshots dir | Configure `chrome.snapshots_dir` before `cli chrome bookmarks snapshot` |
| Scheduled export | Use **`gardusig/pipelines`** workflows — no `scripts/chrome/` in this repo |

Child issues: [#27](https://github.com/gardusig/python-cli/issues/27) (workflow docs), [#28](https://github.com/gardusig/python-cli/issues/28) (snapshots + multi-profile).

## Commands

```bash
cli chrome bookmarks ingest
cli chrome bookmarks ingest --profile Work
cli chrome bookmarks deploy
cli chrome bookmarks merge --dry-run
cli chrome bookmarks merge --source ~/Downloads/export.html
cli chrome bookmarks merge --format json
cli chrome bookmarks snapshot --profile Default
```

## Local workflow catalog

| Workflow | Sequence | Scope |
| --- | --- | --- |
| `chrome-bookmarks-roundtrip` | export → `ingest` → `deploy` → import | Single profile backup |
| `chrome-bookmarks-merge` | export → `merge` | Incremental URL append |
| `chrome-bookmarks-snapshot` | `snapshot` before `merge` | Safety copy |

## Google Photos {#google-photos}

**Epic:** [#50](https://github.com/gardusig/python-cli/issues/50) — file-based ingest from [Google Takeout](https://takeout.google.com/) (no live API in v1).

| Phase | Command | What it does |
| --- | --- | --- |
| Inventory | `chrome photos list` | Albums under `chrome.photos_dir` |
| Ingest | `chrome photos ingest` | Import newest Takeout `.zip` (or `--source`) |
| Status | `chrome photos status` | Summary JSON/table for local inventory |

### Takeout roundtrip

```bash
# In Google Takeout: select Google Photos → create export → download .zip
cli chrome photos ingest --yes
cli chrome photos list --format json
cli chrome photos status --format json
```

Output lands in a **private** path (`chrome.photos_dir`), not this public repo.

### Photos paths

```yaml
chrome:
  photos_dir: ~/git-local/private/photos
  photos_takeout_dir: ~/Downloads   # optional; defaults to chrome.downloads_dir
```

| Env var | Purpose |
| --- | --- |
| `CLI_PHOTOS_DIR` | Override `chrome.photos_dir` |
| `CLI_PHOTOS_TAKEOUT_DIR` | Override Takeout poll directory |
| `CLI_PHOTOS_SOURCE` / `CLI_PHOTOS_FIXTURE` | Explicit Takeout zip/dir (tests/CI) |
| `CLI_SKIP_CHROME_AUTOMATION` | Use newest `.zip` without polling |

Layout after ingest:

```text
photos_dir/
  manifest.json
  albums/
    summer/
      photo.jpg
```

## See also

- [bookmarks.md](bookmarks.md) — short config reference
- [configuration.md](configuration.md) — full config keys
- Epic 07 review [#61](https://github.com/gardusig/python-cli/issues/61) — public CLI hardening for `cli chrome`
