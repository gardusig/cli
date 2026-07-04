# Setup (macOS)

## Install vs verify

| Lane | Purpose | Entry |
| --- | --- | --- |
| **Install** | Run `cli` on macOS from PyPI | `./scripts/pypi/install.sh` |
| **Verify** | Unit + integration gates (CI-equivalent) | `./scripts/test/unit.sh`, `./scripts/test/integration.sh` |

Pytest, coverage, and smoke scripts run **inside** Docker (`cli:integration`) so checks never mutate your checkout.

## Requirements

- Python **3.12+** (`./scripts/pypi/install.sh` or Homebrew)
- `git` on PATH
- `zip` for encrypted tag archives (`encrypted: true` repos)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) for verification (`cli:dev` Linux image)
- Optional: `gh` for GitHub (`cli gh` commands)

## Install from PyPI

Package name on PyPI is **`gardusig-cli`**; the command on PATH is still **`cli`**.

```bash
./scripts/pypi/install.sh
cli --version
```

Installs into `~/.local/share/gardusig-cli/venv`, links `~/.local/bin/cli`, and adds `~/.local/bin` to your shell PATH. Re-run anytime to upgrade to the latest PyPI release.

Pin a version: `./scripts/pypi/install.sh --version 1.0.0`

Config loads from **`~/.config/cli/`** — copy `config/` from this repo as a starting point (`CLI_CONFIG_DIR` to override).

Repo clone path and GitHub project name remain **`cli`** — only the PyPI distribution uses the prefixed name.

## Contributors (repo clone)

Docker gates bootstrap a repo `.venv` inside the container — you do not need a host editable install.

```bash
git clone https://github.com/gardusig/cli.git
cd cli
./scripts/test/unit.sh
./scripts/test/integration.sh
```

Docker gates bootstrap a repo `.venv` inside the container via `scripts/docker/bootstrap.sh` — not a host install path.

`requirements.txt` / `requirements-dev.txt` stay in sync with `pyproject.toml` (checked by `tests/meta/test_project_hygiene.py`).

Maintainers — tag release (PyPI). See [release.md](release.md).

```bash
export PYPI_API_TOKEN='pypi-...'   # or add to .env on host
git tag v1.0.0 && git push origin v1.0.0   # CI runs ./scripts/pypi/release.sh
# or locally (same script as CI):
./scripts/pypi/release.sh
```

| Script | When |
| --- | --- |
| `./scripts/pypi/test.sh` | PR CI — build `1.0.0`, optional TestPyPI |
| `./scripts/pypi/release.sh` | Tag `v*` — production PyPI (Docker `cli:release`) |
| `./scripts/pypi/upload.sh` | Local build + upload (inside container bootstrap) |
| `./scripts/pypi/build.sh` | Build only |

CI runs outside this repository. Configure **`PYPI_API_TOKEN`** (and optional PR secret **`TESTPYPI_API_TOKEN`** for TestPyPI uploads) on the central CI system.

Pull requests and tag `v*` pushes trigger pipelines via `repository_dispatch`.

| Workflow | Trigger | Gate |
| --- | --- | --- |
| `test` | Pull requests | `./scripts/test/unit.sh` then `./scripts/test/integration.sh` |
| `release` | Tags `v*` | PyPI upload (`PYPI_API_TOKEN` secret) |

## Verify (Docker)

Same scripts as GitHub Actions. See [docker.md](docker.md).

```bash
./scripts/docker/build-image.sh   # optional; auto-builds on first run
./scripts/test/unit.sh            # unit gate (≥80% coverage)
./scripts/test/integration.sh     # full pytest + smoke + live docker
```

**Do not** run `pytest`, `pip install -e ".[dev]"`, or `scripts/test/smoke.sh` directly on the host. Integration fixtures (`cli-git-*`, `cli-public-*`, etc.) only run when `CLI_DOCKER_INTEGRATION=1` inside the Docker image; host `pytest` skips `@pytest.mark.integration` tests automatically.

| Script | Scope |
| --- | --- |
| `./scripts/test/unit.sh` | Unit only (`pytest -m "not integration"`) — mocks/stubs, no live PyPI/git fixtures |
| `./scripts/test/integration.sh` | Full suite + smoke + live docker — real builds (PyPI), git fixtures in scratch |

Tests use `CLI_CONFIG_DIR=config/ci` (scratch paths under `.integration-scratch/`, not iCloud).

Remove accidental local artifacts: `cli git clean --yes` (or `./scripts/git/clean.sh --yes`)

## After install

1. `cd` into a git repository for `cli git` commands.
2. Optional: edit `config/config.yaml` → `backup.repositories` for `cli drive status` / `drive ingest`.
3. Chrome `bookmarks deploy` (local → browser) needs a prior `bookmarks ingest` into your configured `chrome.bookmarks_file`.

See [configuration.md](configuration.md) and README **Configuration**.

## Troubleshooting

- **`git` not in a repository** — run commands from a git worktree root.
- **Refusing to push** — pass `--yes` to confirm: `cli git push --yes`.
- **Dirty tree on `main`** — pass `--yes` to destructive align/reset commands.
- **`cli git start` deleted my files** — use `--no-prep` to branch in place; default `start` aligns main first.
- **`docker is not installed`** when testing — install Docker Desktop; verification does not use host Python.
- **`command not found: cli`** — run `./scripts/pypi/install.sh`, then open a new terminal or `source ~/.zprofile`.
- **`cli git review` fails** — full review calls `./scripts/test/unit.sh`; use `--quick` for shell syntax only.
