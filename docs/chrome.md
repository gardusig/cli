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

**Deferred** ([#50](https://github.com/gardusig/python-cli/issues/50)). Epic 02 keeps Chrome integration to **file upload/ingest** (bookmark HTML). Google Photos album retrieval is out of scope until a future upload contract is defined.

`cli chrome photos` exits with a clear defer message. Use bookmark commands above for supported workflows.

## See also

- [bookmarks.md](bookmarks.md) — short config reference
- [configuration.md](configuration.md) — full config keys
- Epic 07 review [#61](https://github.com/gardusig/python-cli/issues/61) — public CLI hardening for `cli chrome`
