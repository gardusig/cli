# cli

Linux-first CLI helper: **`cli git`** · **`cli lint`** · **`cli pipeline`** · **`cli release`**.

## Status

[![PyPI version](https://img.shields.io/pypi/v/gardusig-cli?label=PyPI)](https://pypi.org/project/gardusig-cli/)
[![Python](https://img.shields.io/pypi/pyversions/gardusig-cli?label=Python)](https://pypi.org/project/gardusig-cli/)
[![License: MIT](https://img.shields.io/pypi/l/gardusig-cli?label=License)](https://github.com/gardusig/cli/blob/main/LICENSE)

This README is the **long description on [PyPI](https://pypi.org/project/gardusig-cli/)** and the **GitHub project page** — badges link to the same sources of truth on both sites.

| Where | What you get |
| --- | --- |
| **GitHub** ([gardusig/cli](https://github.com/gardusig/cli)) | Source and issues — **application code only** |
| **PyPI** (`pip install gardusig-cli`) | Installable package; console command is `cli` |
| **CI / release** | In-repo [`Dockerfile`](Dockerfile) + [`.github/workflows/`](.github/workflows/) (TestPyPI on PR, PyPI on tag) |
| **Unit coverage** | [`coverage-unit.ini`](coverage-unit.ini) — `cli` package, ≥80% |

Install from PyPI when you only need the tool; clone the repo when you want config and product scripts.

## Naming

| Context | Identifier |
| --- | --- |
| **GitHub repo** | [gardusig/cli](https://github.com/gardusig/cli) |
| **PyPI package** | `gardusig-cli` — `pip install gardusig-cli` |
| **Console command** | `cli` (unchanged after PyPI install) |
| **Python import** | `src` |

The repo stays **`cli`**; only the published distribution name on PyPI is **`gardusig-cli`** (`cli` is taken on PyPI).

## Requirements

| Tool | Needed for |
| --- | --- |
| **Linux terminal** | Primary runtime target |
| **Python 3.12+** | `pip install gardusig-cli` |
| **git** | `cli git` (run from inside a repository) |
| **zip** | Encrypted tag archives (`cli drive ingest` on `encrypted: true` repos) |
| **Docker Engine** | Verification — `cli test python unit .` and `cli test python integration .` in Docker |

Install Python and git with your Linux package manager:

```bash
sudo apt-get install python3 git
```

Optional: `gh` (GitHub CLI) for `cli gh` and `cli opencode gh` workflows.

## Configuration (global)

Cli reads **`config/config.yaml`** in the clone, or **`~/.config/cli/`** after install. Override the directory with `CLI_CONFIG_DIR`.

Copy the bundled `config/` tree and edit paths for your machine before daily use:

| Setting | Config key | Purpose |
| --- | --- | --- |
| **Git repositories** | `backup.repositories[].path` | Repos for `cli drive ingest` / `drive status` |
| **Tag zip folder** | `backup.tags_dir` | Local store (default: iCloud `git-tags/`) — source for `drive upload` |
| **Cloud upload roots** | `drives.yaml` → `google` / `onedrive` / `proton` | Remote folder names per provider |
| **Notion task root** | `notion.task_root` | Private `header/` + `body/` task files |
| **Notion pairs manifest** | `notion.pairs_file` | `config/notion/tasks.pairs.json` in this repo |
| **Notion database** | `notion.database_id` | Existing board ID + `NOTION_TOKEN` env |
| **Backup zip password** | `BACKUP_ZIP_PASSWORD` env | Encrypted repos (`encrypted: true` in `backup.repositories`) |
| **Chrome bookmarks file** | `chrome.bookmarks_file` | HTML backup (`chrome bookmarks ingest`) |
| **Chrome downloads** | `chrome.downloads_dir` | Folder polled when ingesting from Chrome |

Example `config.yaml`:

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/cli
    - path: ~/git-local/my-other-repo

notion:
  database_id: your-notion-database-id
  task_root: ~/git-local/private/database/tasks
  pairs_file: config/notion/tasks.pairs.json

chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

Test fixtures (not for production) live under `tests/fixtures/notion/tasks` and `tests/fixtures/bookmarks.html`.

Cloud providers: `config/drives.yaml`. Notion token: **`export NOTION_TOKEN=...`** (never commit).

Environment overrides (optional): `CLI_BOOKMARKS_FILE`, `CLI_DOWNLOADS_DIR`, `CLI_CONFIG_DIR`, `NOTION_TOKEN`.

## Install

Install the latest **`gardusig-cli`** release from PyPI (no repo clone required):

```bash
pip install gardusig-cli
cli --version
cli git --help
```

Upgrade anytime: re-run `pip install gardusig-cli`

Config: **`~/.config/cli/`** (copy `config/` from this repo as a starting point; override with `CLI_CONFIG_DIR`).

**Contributors** — verification runs in Docker only (`cli test python unit .`, `cli test python integration .`).

## Common git commands

Run from inside a repository (`cd` into the repo first).

| Task | Command |
| --- | --- |
| **Sync main** (before/after work) | `cli git reset --yes` (`--delete-merged` to prune; `--main-only` to skip branch prompt) |
| **Start issue** (align main + branch) | `cli git start issue-9-slug --yes` |
| **Ship to main** (personal backup) | `cli ship --yes` |
| **During work** (feature branch) | `cli git push --yes` |
| **Wip branch from main** | `cli git push --yes --branch` |
| Branch in place (no align) | `cli git start [name] --no-prep` |
| Commit only | `cli git commit` |
| Sync feature branch | `cli git pull` |
| Delete merged branch | `cli git branch delete BRANCH --yes` |
| Delete merged branches | `cli git branch delete --merged --yes` |
| Delete all branches (keep `main`) | `cli git branch delete --all --yes` |
| Clear all branches (keep `main`) | `cli git branch clear --yes` |
| Tag on main (default: today) | `cli git tag` · `cli git tag list` · `cli git tag push` |
| Zip one tag (cwd repo) | `cli git zip` · `cli git zip TAG` |

Short alias: `cli g push --yes` == `cli git push --yes`.

**Safety:** destructive actions (reset, clean, delete, push) require `--yes` or an interactive confirmation. Default `cli git start` aligns main then branches; pass `--no-prep` to branch from the current state.

## Drive (`cli drive`)

Local hub: **iCloud** `git-tags/{repo}/{repo}-{tag}.zip` (via `backup.tags_dir`). Cloud: append-only upload to Google Drive and OneDrive (`GOOGLE_DRIVE_TOKEN`, `ONEDRIVE_TOKEN`). Proton is deferred.

| Task | Command |
| --- | --- |
| **Status** (git tags vs local zips) | `cli drive status` · `cli drive status --replicas` |
| **Ingest** (zip all tags → local store) | `cli drive ingest` (all repos in config) or `cli drive ingest PATH` |
| List local zips | `cli drive list` · `cli drive list PATH` |
| Delete local zip | `cli drive delete PATH TAG --yes` |
| **Upload** to cloud | `cli drive upload` · `cli drive upload google` · `onedrive` |
| **Download** from cloud | `cli drive download` · `cli drive download google` |
| **Deploy** (cloud + USB) | `cli drive deploy` · `--dry-run` · `--format json` |
| **Sync** (ingest all + deploy all) | `cli drive sync` |

Typical end-of-day:

```bash
cli git tag --yes && cli git zip    # single repo (cwd)
cli drive upload                        # push missing zips to cloud
```

Multi-repo:

```bash
cli drive sync                          # ingest all repos + upload all clouds
# or step by step:
cli drive ingest
cli drive status
cli drive upload
```

`git zip` is the quick path for the current repo; `drive ingest` iterates configured repositories (or one `PATH`). See [docs/drive.md](docs/drive.md).

## Chrome (`cli chrome`)

Bookmark file ingest/deploy (manual browser export/import). See [docs/chrome.md](docs/chrome.md).

| Task | Command |
| --- | --- |
| **Ingest** export → backup | `cli chrome bookmarks ingest` |
| **Merge** new URLs | `cli chrome bookmarks merge` · `--dry-run` |
| **Snapshot** safety copy | `cli chrome bookmarks snapshot` |
| **Deploy** validate for import | `cli chrome bookmarks deploy` |

```bash
cli chrome bookmarks ingest
cli chrome bookmarks snapshot
cli chrome bookmarks merge --dry-run
cli chrome bookmarks deploy
```

Google Photos: `cli chrome photos ingest` imports Google Takeout exports into a configured private `photos_dir`.

See also [docs/bookmarks.md](docs/bookmarks.md).

## Notion (`cli notion`)

Local tasks: **`notion.task_root`** (private header/body) + **`notion.pairs_file`** (`config/notion/tasks.pairs.json`). Auth: **`NOTION_TOKEN`** + `notion.database_id`.

| Command | Purpose |
| --- | --- |
| `cli notion pairs build` | Scan header/ + body/ → `tasks.pairs.json` |
| `cli notion ingest` | Notion → local pairs |
| `cli notion deploy --yes` | Local pairs → Notion (archives board first by default) |
| `cli notion sync --yes` | Ingest from Notion, then deploy local tasks |
| `cli notion cleanup --yes` | Archive all database pages |

See [docs/notion.md](docs/notion.md).

## Docker

Local Docker monitor and cleanup (requires `docker` on PATH; no container start):

| Task | Command |
| --- | --- |
| **Dashboard** (CPU, memory, storage) | `cli docker top` |
| **By domain** | `cli docker stats --by cpu` / `memory` / `storage` |
| **Storage lists** | `cli docker images` · `cli docker containers` · `cli docker df` |
| **Stop running** | `cli docker stop --yes` |
| **Delete containers** | `cli docker container-delete --yes` |
| **Prune images** | `cli docker image-delete --yes` (`--all-images` for all unused) |
| **Full reset** | `cli docker reset --yes` |
| Targeted cleanup | `cli docker clean containers --yes` · `clean images` · `clean all` |

Docker cleanup is exposed through `cli docker ...`; CI Docker stages live in this repo's root `Dockerfile` (`scripts/ci/*.sh` entrypoints).

Destructive commands use the write gate; pass `--yes` in scripts.

## Verify (Docker)

Requires Docker Engine on Linux. Stages mirror central CI:

```bash
export BASE_VERSION="$(bash scripts/ci/host-base-version.sh origin/main)"
docker build --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build --target unit-test .
```

## CI and release

Thin GitHub Actions workflows live in [`.github/workflows/`](.github/workflows/) (`pull-request.yaml`, `release.yaml`). Each job only runs `docker build --target …`; logic is in the root `Dockerfile` and `scripts/ci/*.sh`.

| Trigger | What runs |
| --- | --- |
| **Pull request** | `version-check` → `unit-test` → `pypi-test` → `integration-test` + `testpypi-consumer` |
| **Tag** `v*` | `docker build --target release` then `pypi-consumer` |

Configure secrets on **`gardusig/cli`**: `TESTPYPI_API_TOKEN`, `PYPI_API_TOKEN`.

Details: [docs/release.md](docs/release.md) · [docs/ci-workflows.md](docs/ci-workflows.md) · [docs/development.md](docs/development.md).

## Development

Clone **`gardusig/cli`** directly — you do not need the [`gardusig/gardusig`](https://github.com/gardusig/gardusig) profile monorepo to work on this package.

```bash
git clone git@github.com:gardusig/cli.git && cd cli
uv sync
.venv/bin/python -m pytest tests/meta/ -q
```

## Docs

- [Development](docs/development.md)
- [Release](docs/release.md)
- [Git commands](docs/git.md)
- [GitHub (`cli gh`)](docs/gh.md)
- [Drive (local + cloud)](docs/drive.md)
- [Chrome](docs/chrome.md) · [Notion](docs/notion.md)
- [Docker integration](docs/docker.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## Related

- [OpenCode](docs/opencode.md) — `cli opencode` AI entry point
- [Hub operator](docs/hub-operator.md) — headless ship lane + CI runner
