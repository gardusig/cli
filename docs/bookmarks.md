# Chrome bookmarks

See **[chrome.md](chrome.md)** for the full Epic 02 command reference, workflow catalog, and pipeline boundary.

Part of **`cli chrome bookmarks`** ([issue #24](https://github.com/gardusig/python-cli/issues/24)). Legacy shell scripts ([#1](https://github.com/gardusig/python-cli/issues/1)) are superseded by Python commands.

Local-centric naming (aligned with **`cli drive`**): **ingest** = into the configured backup file; **deploy** = validate the backup for browser import.

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

## Environment overrides

| Env var | Purpose |
| --- | --- |
| `CLI_BOOKMARKS_FILE` | Override `chrome.bookmarks_file` (default profile) |
| `CLI_DOWNLOADS_DIR` | Poll folder for HTML exports |
| `CLI_BOOKMARKS_SOURCE` / `CLI_BOOKMARKS_FIXTURE` | Explicit ingest/merge source |
| `CLI_SKIP_CHROME_AUTOMATION` | CI/headless: skip polling, use newest or fixture |

Use `--profile NAME` when `chrome.profiles` defines multiple bookmark files ([#28](https://github.com/gardusig/python-cli/issues/28)).

Scheduled jobs and shell wrappers belong in **`gardusig/pipelines`**, not this repo ([#27](https://github.com/gardusig/python-cli/issues/27)).

## Commands

| Direction | CLI |
| --- | --- |
| Exported HTML → local | `cli chrome bookmarks ingest` |
| Merge new URLs into backup | `cli chrome bookmarks merge` |
| Timestamped safety copy | `cli chrome bookmarks snapshot` |
| Local backup → browser import | `cli chrome bookmarks deploy` |

Hidden legacy: `import` / `export` on `chrome bookmarks`, and `cli bookmarks …` (top-level).

## Requirements

- Linux terminal or CI environment
- A bookmarks HTML export in `chrome.downloads_dir` or an explicit `CLI_BOOKMARKS_SOURCE`
- `CLI_SKIP_CHROME_AUTOMATION=1` in CI (uses fixture/newest file, no polling)
