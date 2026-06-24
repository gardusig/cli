# Configuration layout

| Path | Role |
| --- | --- |
| [`config.yaml`](config.yaml) | Default dev settings (backup paths, Notion, Chrome) |
| [`drives.yaml`](drives.yaml) | Cloud drive upload targets (shared by dev and CI) |
| [`ci/config.yaml`](ci/config.yaml) | Docker test harness overrides (`CLI_CONFIG_DIR=config/ci`) |
| [`notion/`](notion/) | Task pair manifest + header/body scaffolds |
| [`contest/`](contest/) | Contest validate defaults + generator/brute templates |

## CI vs dev

`config/ci/` contains **only** overrides needed inside Docker test runs (fixture paths, fake database id, scratch `tags_dir`). It does **not** duplicate `drives.yaml` — `load_config` falls back to the parent file when `config/ci/drives.yaml` is absent.

`CLI_CONFIG_DIR=config/ci` is set automatically in Docker test scripts and in `tests/conftest.py` (autouse) so integration never writes to iCloud or home config paths.

## Contest templates vs test fixtures

- [`contest/templates/`](contest/templates/) — copy-paste scaffolds for real problems (`lib.py`, `generator.py`, `brute.py`)
- [`tests/fixtures/contest/toy/`](../tests/fixtures/contest/toy/) — working toy problem for harness tests; imports `lib` from `config/contest/templates/`

## Notion manifests

- [`notion/tasks.pairs.json`](notion/tasks.pairs.json) — production manifest (paths relative to private `notion.task_root`)
- `tests/fixtures/notion/**/tasks.pairs.json` — isolated test workspaces (not duplicates of config)
