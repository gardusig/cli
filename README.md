# cli

Linux-first CLI helper: **`cli git`** · **`cli configure`** · **`cli drive`** · **`cli release`**.

## Status

[![PyPI version](https://img.shields.io/pypi/v/gardusig-cli?label=PyPI)](https://pypi.org/project/gardusig-cli/)
[![Python](https://img.shields.io/pypi/pyversions/gardusig-cli?label=Python)](https://pypi.org/project/gardusig-cli/)
[![License: MIT](https://img.shields.io/pypi/l/gardusig-cli?label=License)](https://github.com/gardusig/cli/blob/main/LICENSE)

This README is the **long description on [PyPI](https://pypi.org/project/gardusig-cli/)** and the **GitHub project page** — badges link to the same sources of truth on both sites.

| Where | What you get |
| --- | --- |
| **GitHub** ([gardusig/cli](https://github.com/gardusig/cli)) | Source, issues, CI workflows |
| **PyPI** (`pip install gardusig-cli`) | Installable package; console command is `cli` |
| **CI / release** | [`.github/workflows/`](.github/workflows/) + `docker/*.dockerfile` |
| **Unit coverage** | [`coverage-unit.ini`](coverage-unit.ini) — `cli` package, ≥80% |

Install from PyPI when you only need the tool; clone this repo when developing (tests, CI scripts, docs).

## Naming

| Context | Identifier |
| --- | --- |
| **GitHub repo** | [gardusig/cli](https://github.com/gardusig/cli) |
| **PyPI package** | `gardusig-cli` — `pip install gardusig-cli` |
| **Console command** | `cli` (unchanged after PyPI install) |
| **Python import** | `src` |

The PyPI wheel ships **`src/`** only (plus bundled defaults under `src/data/`). User settings live in `~/.config/cli` via **`cli configure`** — no repo `config/` tree is required.

The GitHub repo is named **`cli`**; only the published PyPI name is **`gardusig-cli`**.

## Requirements

| Tool | Needed for |
| --- | --- |
| **Linux terminal** | Primary runtime target |
| **Python 3.12+** | `pip install gardusig-cli` |
| **git** | `cli git` (run from inside a repository) |
| **zip** | Encrypted tag archives (`cli drive ingest` on `encrypted: true` repos) |
| **Docker Engine** | CI verification and optional `cli test python unit .` in Docker |

Install Python and git with your Linux package manager:

```bash
sudo apt-get install python3 git
```

## Configuration (global)

Fresh install uses **code defaults only**. Bootstrap with:

```bash
cli configure init
cli configure set notion.task_root ~/your/tasks
```

User config path (`cli configure path`):

- Linux: `~/.config/cli` (or `$XDG_CONFIG_HOME/cli`)
- macOS: `~/Library/Application Support/cli`

Contributors and CI: `CLI_CONFIG_DIR=tests/fixtures/config` + `CLI_PROFILE=test`.

| Setting | Config key | Purpose |
| --- | --- | --- |
| **Git repositories** | `backup.repositories[].path` | Repos for `cli drive ingest` / `drive status` |
| **Tag zip folder** | `backup.tags_dir` | Local zip store — set via `cli configure set backup.tags_dir` |
| **Cloud upload roots** | `drives.yaml` → `google` / `onedrive` / `proton` | Remote folder names per provider |
| **Notion task root** | `notion.task_root` | Private `header/` + `body/` task files |
| **Notion pairs manifest** | `notion.pairs_file` | Path under your task root or an absolute path |
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
  task_root: ~/git-local/private/configured/tasks
  pairs_file: tasks.pairs.json

chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

Test fixtures (not for production) live under `tests/fixtures/notion/tasks` and `tests/fixtures/bookmarks.html`.

Cloud providers: `drives.yaml` in your config dir (`cli configure path`). Notion token: **`cli configure set notion.token --stdin`** or `export NOTION_TOKEN=...`.

Environment overrides (optional): `CLI_BOOKMARKS_FILE`, `CLI_DOWNLOADS_DIR`, `CLI_CONFIG_DIR`, `CLI_PROFILE`, `NOTION_TOKEN`. Secrets: **`cli configure set <key> --stdin`** or export the env var (see [docs/secrets.md](docs/secrets.md)).

## Install

Install the latest **`gardusig-cli`** release from PyPI (no repo clone required):

```bash
pip install gardusig-cli
cli --version
cli git --help
```

Upgrade anytime: re-run `pip install gardusig-cli`

Config: run **`cli configure init`**, then **`cli configure set …`** (see [Configuration](#configuration-global) and [docs/configure.md](docs/configure.md)). Repo checkout for tests/CI: `CLI_CONFIG_DIR=tests/fixtures/config` + `CLI_PROFILE=test`.

**`cli configure`** is the supported entry point for paths and secrets. **`cli config`** remains as a deprecated alias (forwards to `configure`).

**Contributors** — run the PR pipeline locally or in CI:

```bash
bash scripts/local/compare-docker-pipelines.sh   # host vs docker/pull-request.dockerfile
docker build -f docker/pull-request.dockerfile --target unit-test .
```

See [docs/development.md](docs/development.md) and [docs/ci-workflows.md](docs/ci-workflows.md).

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
| Tag on main (suggests next `X.Y.Z`) | `cli git tag` · `cli git tag list` · `cli git tag push` |
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

`git zip` is the quick path for the current repo; `drive ingest` iterates configured repositories (or one `PATH`). See [docs/drive.md](docs/drive.md) · [issue #4](https://github.com/gardusig/cli/issues/4).

## Chrome (`cli chrome`)

Bookmark file ingest/deploy (manual browser export/import). See [docs/chrome.md](docs/chrome.md) · epic [#24](https://github.com/gardusig/cli/issues/24).

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

Google Photos ([#50](https://github.com/gardusig/cli/issues/50)): `cli chrome photos ingest` imports Google Takeout exports into a configured private `photos_dir`.

See also [docs/bookmarks.md](docs/bookmarks.md).

## Notion (`cli notion`)

Local tasks: **`notion.task_root`** (private header/body) + **`notion.pairs_file`** (manifest path). Auth: **`NOTION_TOKEN`** + `notion.database_id`.

| Command | Purpose |
| --- | --- |
| `cli notion pairs build` | Scan header/ + body/ → `tasks.pairs.json` |
| `cli notion ingest` | Notion → local pairs |
| `cli notion deploy --yes` | Local pairs → Notion (archives board first by default) |
| `cli notion sync --yes` | Ingest from Notion, then deploy local tasks |
| `cli notion cleanup --yes` | Archive all database pages |

See [docs/notion.md](docs/notion.md) · epic [#2](https://github.com/gardusig/cli/issues/2) · children [#20](https://github.com/gardusig/cli/issues/20)–[#23](https://github.com/gardusig/cli/issues/23).

## Docker monitor (`cli docker`)

Local Docker monitor and cleanup (requires `docker` on PATH; does not start containers or run CI images):

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

Docker cleanup is exposed through `cli docker ...`. CI Docker stages use `docker/pull-request.dockerfile` and `docker/release.dockerfile` (see [docs/docker.md](docs/docker.md)).

Destructive commands use the write gate; pass `--yes` in scripts.

## Verify CI (Docker builds)

PR and release **CI images** (not the `cli docker` commands above). Requires Docker Engine.

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"
docker build -f docker/pull-request.dockerfile --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build -f docker/pull-request.dockerfile --target unit-test .
```

Or compare host scripts vs both Dockerfiles:

```bash
bash scripts/local/compare-docker-pipelines.sh
```

## CI and release

This repo owns PR and release pipelines under [`.github/workflows/`](.github/workflows/).

| Trigger | Workflow | Pipeline |
| --- | --- | --- |
| **Pull request → `main`** | `pull-request.yaml` | Resolve → version check → unit tests → TestPyPI → consumer smoke |
| **Tag push `X.Y.Z`** | `release.yaml` | PyPI publish → Docker Hub image → GitHub release |

Dockerfiles: `docker/pull-request.dockerfile` (build from source), `docker/release.dockerfile` (PyPI + runtime).

Secrets on `gardusig/cli`: `TESTPYPI_API_TOKEN`, `PYPI_API_TOKEN`, `DOCKERHUB_TOKEN`, `DOCKERHUB_USERNAME`.

Release: bump version in `pyproject.toml`, merge to `main`, then `git tag 1.0.8 && git push origin 1.0.8` (bare semver, no `v` prefix).

Details: [docs/release.md](docs/release.md) · [docs/setup.md](docs/setup.md) · [docs/ci-workflows.md](docs/ci-workflows.md).

## Docs

- [Setup](docs/setup.md) · [Install](docs/install.md)
- [Configure](docs/configure.md)
- [Configuration](docs/configuration.md) · [Secrets](docs/secrets.md)
- [Release](docs/release.md)
- [CI workflows](docs/ci-workflows.md)
- [Development](docs/development.md)
- [Git commands](docs/git.md)
- [Drive (local + cloud)](docs/drive.md)
- [Chrome](docs/chrome.md) · [Notion](docs/notion.md)
- [Docker integration](docs/docker.md)
- [GitHub (`cli gh`)](docs/gh.md)
- [Architecture](docs/architecture.md)

## Related

- [OpenCode](docs/opencode.md) — `cli opencode` AI entry point
- Cloud drive epic: [cli #4](https://github.com/gardusig/cli/issues/4)
- Bootstrap spec: [cli #3](https://github.com/gardusig/cli/issues/3)
- Chrome: [cli #24](https://github.com/gardusig/cli/issues/24) · bookmarks [#1](https://github.com/gardusig/cli/issues/1) superseded
- Docker integration: [cli #9](https://github.com/gardusig/cli/issues/9)
