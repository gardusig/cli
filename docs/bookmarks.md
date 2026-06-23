# Chrome bookmarks

Part of **`cli chrome bookmarks`** ([issue #1](https://github.com/gardusig/cli/issues/1) · epic [#24](https://github.com/gardusig/cli/issues/24)).

Local-centric naming (aligned with **`cli drive`**): **ingest** = into the repo; **deploy** = out to Chrome.

## Configuration

```yaml
chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

## Commands

| Direction | CLI | Script |
| --- | --- | --- |
| Chrome → local | `cli chrome bookmarks ingest` | `./scripts/chrome/ingest.sh` |
| Local → Chrome | `cli chrome bookmarks deploy` | `./scripts/chrome/deploy.sh` |

Hidden legacy: `import` / `export` on `chrome bookmarks`, and `cli bookmarks …` (top-level).

## Requirements

- macOS with Google Chrome
- Accessibility permissions when GUI automation runs
