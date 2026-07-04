# cli

macOS CLI: **`cli git`** · **`cli drive`** · **`cli chrome`** · **`cli notion`**.

## Status

[![PyPI version](https://img.shields.io/pypi/v/gardusig-cli?label=PyPI)](https://pypi.org/project/gardusig-cli/)
[![Python](https://img.shields.io/pypi/pyversions/gardusig-cli?label=Python)](https://pypi.org/project/gardusig-cli/)
[![License: MIT](https://img.shields.io/pypi/l/gardusig-cli?label=License)](https://github.com/gardusig/python-cli/blob/main/LICENSE)

This README is the **long description on [PyPI](https://pypi.org/project/gardusig-cli/)** and the **GitHub project page** — badges link to the same sources of truth on both sites.

| Where | What you get |
| --- | --- |
| **GitHub** ([gardusig/python-cli](https://github.com/gardusig/python-cli)) | Source and issues — **application code only** |
| **PyPI** (`pip install gardusig-cli`) | Installable package; console command is `cli` |
| **CI / release** | External Docker pipelines — not in this repo |
| **Unit coverage** | [`coverage-unit.ini`](coverage-unit.ini) — `cli` package, ≥80% |

Install from PyPI when you only need the tool; clone the repo when you want config and product scripts.

## Naming

| Context | Identifier |
| --- | --- |
| **GitHub repo** | [gardusig/python-cli](https://github.com/gardusig/python-cli) |
| **PyPI package** | `gardusig-cli` — `pip install gardusig-cli` |
| **Console command** | `cli` (unchanged after PyPI install) |
| **Python import** | `src` |

The repo stays **`cli`**; only the published distribution name on PyPI is **`gardusig-cli`** (`cli` is taken on PyPI).

## Requirements

| Tool | Needed for |
| --- | --- |
| **macOS** | Primary target for local use |
| **Python 3.12+** | `./scripts/pypi/install.sh` or Homebrew |
| **[Homebrew](https://brew.sh/)** | Recommended way to install Python and git on macOS |
| **git** | `cli git` (run from inside a repository) |
| **zip** | Encrypted tag archives (`cli drive ingest` on `encrypted: true` repos) |
| **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** | Verification — `./scripts/test/unit.sh` and `./scripts/test/integration.sh` in Docker |

Install Python and git with Homebrew:

```bash
brew install python@3.12 git
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
  task_root: ~/git-local/private/configured/tasks
  pairs_file: config/notion/tasks.pairs.json

chrome:
  profile: Default
  bookmarks_file: ~/git-local/private/bookmarks/bookmarks.html
  downloads_dir: ~/Downloads
```

Test fixtures (not for production) live under `tests/fixtures/notion/tasks` and `tests/fixtures/bookmarks.html`.

Cloud providers: `config/drives.yaml`. Notion token: **`export NOTION_TOKEN=...`** (never commit).

Environment overrides (optional): `CLI_BOOKMARKS_FILE`, `CLI_DOWNLOADS_DIR`, `CLI_CONFIG_DIR`, `NOTION_TOKEN`.

## Install (macOS)

Install the latest **`gardusig-cli`** release from PyPI (no repo clone required):

```bash
./scripts/pypi/install.sh
# open a new terminal OR: source ~/.zprofile
cli --version
cli git --help
```

Upgrade anytime: re-run `./scripts/pypi/install.sh`

Config: **`~/.config/cli/`** (copy `config/` from this repo as a starting point; override with `CLI_CONFIG_DIR`).

**Contributors** — verification runs in Docker only (`./scripts/test/unit.sh`, `./scripts/test/integration.sh`).

## Common git commands

Run from inside a repository (`cd` into the repo first).

| Task | Command |
| --- | --- |
| **Sync main** (before/after work) | `cli git reset --yes` (`--delete-merged` to prune; `--main-only` to skip branch prompt) |
| **Start issue** (align main + branch) | `cli git start issue-9-slug --yes` |
| **During work** (add + commit + push) | `cli git push --yes` (on `main`, starts random branch first) |
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

Shell wrappers: `scripts/git/` (e.g. `./scripts/git/review.sh`). See [docs/git.md](docs/git.md).

**Safety:** destructive actions (reset, clean, delete, push) require `--yes` or an interactive confirmation. Default `cli git start` aligns main then branches; pass `--no-prep` to branch from the current state.

## Drive (`cli drive`)

Local hub: **iCloud** `git-tags/{repo}/{repo}-{tag}.zip` (via `backup.tags_dir`). Cloud: append-only upload to Google Drive, OneDrive, Proton.

| Task | Command |
| --- | --- |
| **Status** (git tags vs local zips) | `cli drive status` |
| **Ingest** (zip all tags → local store) | `cli drive ingest` (all repos in config) or `cli drive ingest PATH` |
| List local zips | `cli drive list` · `cli drive list PATH` |
| Delete local zip | `cli drive delete PATH TAG --yes` |
| **Upload** to cloud | `cli drive upload` · `cli drive upload google` · `onedrive` · `proton` |
| **Sync** (ingest all + upload all) | `cli drive sync` |

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

Shell wrappers: `scripts/drive/` (`status.sh`, `ingest.sh`, `upload.sh`, `sync.sh`).

## Chrome (`cli chrome`)

Browser integrations; **bookmarks** is the first subcommand. Path: **`chrome.bookmarks_file`** in config.

| Direction | Command |
| --- | --- |
| **Chrome → local** | `cli chrome bookmarks ingest` |
| **Local → Chrome** | `cli chrome bookmarks deploy` |

```bash
cli chrome bookmarks ingest   # Chrome → local HTML file
cli chrome bookmarks deploy   # local file → Chrome
```

Shell wrappers: `./scripts/chrome/ingest.sh` · `./scripts/chrome/deploy.sh` (deprecated: `import.sh` / `export.sh`).

See [docs/bookmarks.md](docs/bookmarks.md) · epic [#24](https://github.com/gardusig/cli/issues/24) (shell scripts: [#1](https://github.com/gardusig/cli/issues/1)).

## Notion (`cli notion`)

Local tasks: **`notion.task_root`** (private header/body) + **`notion.pairs_file`** (`config/notion/tasks.pairs.json`). Auth: **`NOTION_TOKEN`** + `notion.database_id`.

| Command | Purpose |
| --- | --- |
| `cli notion pairs build` | Scan header/ + body/ → `tasks.pairs.json` |
| `cli notion ingest` | Notion → local pairs |
| `cli notion deploy --yes` | Local pairs → Notion (archives board first by default) |
| `cli notion sync --yes` | Ingest from Notion, then deploy local tasks |
| `cli notion cleanup --yes` | Archive all database pages |

See [docs/notion.md](docs/notion.md) · epic [#2](https://github.com/gardusig/cli/issues/2) · children [#20](https://github.com/gardusig/cli/issues/20)–[#23](https://github.com/gardusig/cli/issues/23).

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

Shell wrappers live in `scripts/docker/` (e.g. `./scripts/docker/reset.sh --yes`).

Destructive commands use the write gate; pass `--yes` in scripts.

## Verify (Docker)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) on macOS (or Docker Engine on Linux). The `cli:dev` Linux image is the only supported test environment:

## CI and release

CI and Docker run **outside this repository** (central DevOps). This repo has no `.github/` workflows or `Dockerfile`.

| Trigger | What runs |
| --- | --- |
| **Pull request** | Unit → integration → PyPI packaging (Docker) |
| **Tag** `v*` | Publish `gardusig-cli` to PyPI |

Configure release secrets on the central CI system (`PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN`). Tag pushes trigger release via `repository_dispatch`.

Details: [docs/release.md](docs/release.md) · [docs/setup.md](docs/setup.md).

## Docs

- [Setup](docs/setup.md)
- [Git commands](docs/git.md)
- [GitHub (`cli gh`)](docs/gh.md)
- [Drive (local + cloud)](docs/drive.md)
- [Chrome](docs/bookmarks.md) · [Notion](docs/notion.md)
- [Docker integration](docs/docker.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## Related

- [OpenCode](docs/opencode.md) — `cli opencode` AI entry point
- Cloud drive epic: [cli #4](https://github.com/gardusig/cli/issues/4)
- Bootstrap spec: [cli #3](https://github.com/gardusig/cli/issues/3)
- Chrome: [cli #24](https://github.com/gardusig/cli/issues/24) · bookmarks scripts [#1](https://github.com/gardusig/cli/issues/1)
- Docker integration: [cli #9](https://github.com/gardusig/cli/issues/9)
