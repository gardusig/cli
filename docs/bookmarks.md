# Chrome bookmarks

Part of **`shuttle chrome bookmarks`** ([issue #1](https://github.com/gardusig/shuttle-cli/issues/1) · epic [#24](https://github.com/gardusig/shuttle-cli/issues/24)).

Local-centric naming (aligned with **`shuttle drive`**): **ingest** = into the repo; **deploy** = out to Chrome.

## Configuration

```yaml
chrome:
  profile: Default
  bookmarks_file: ~/git-local/shuttle-cli/data/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

## Commands

| Direction | CLI | Script |
| --- | --- | --- |
| Chrome → local | `shuttle chrome bookmarks ingest` | `./scripts/chrome/ingest.sh` |
| Local → Chrome | `shuttle chrome bookmarks deploy` | `./scripts/chrome/deploy.sh` |

Hidden legacy: `import` / `export` on `chrome bookmarks`, and `shuttle bookmarks …` (top-level).

## Requirements

- macOS with Google Chrome
- Accessibility permissions when GUI automation runs
