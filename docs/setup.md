# Setup (macOS)

## Install vs verify

| Lane | Purpose | Entry |
| --- | --- | --- |
| **Install** | Run `cli` on macOS | `./scripts/bootstrap.sh` or `./scripts/install.sh` |
| **Verify** | Unit + integration gates (CI-equivalent) | `./scripts/test-unit.sh`, `./scripts/test-integration.sh` |

Local `.venv` gets **runtime** dependencies only. Pytest, coverage, and smoke scripts run **inside** Docker (`cli:unit` / `cli:integration`) so checks never mutate your checkout.

## Requirements

- Python **3.12+** (local CLI via `bootstrap.sh` / `install.sh`)
- `git` on PATH
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) for verification (`cli:dev` Linux image)
- Optional: `gh` for GitHub (used by cursor-skills, not cli)

## Local install (dev — current shell only)

For development in this repo. Requires `source .venv/bin/activate` in each terminal.

```bash
git clone https://github.com/gardusig/cli.git
cd cli
./scripts/bootstrap.sh
source .venv/bin/activate
python -m cli --help
```

Manual venv (runtime only): `pip install -r requirements.txt` then `pip install -e .`  
Host dev tools (not needed for Docker verify): `pip install -r requirements-dev.txt` or `pip install -e ".[dev]"`.

## User install (global — any terminal)

Installs `cli` to `~/.local/bin` and adds it to your shell PATH (`~/.zprofile` / `~/.zshrc`).

```bash
./scripts/install.sh
# open a new terminal OR: source ~/.zprofile
cli --version
cli git --help
```

Config loads from the repo `config/` directory (editable install) — no `cd` into the clone required.

## Verify (Docker)

Same scripts as GitHub Actions. See [docker.md](docker.md).

```bash
./scripts/docker/build-image.sh   # optional; auto-builds on first run
./scripts/test-unit.sh            # unit gate (≥80% coverage)
./scripts/test-integration.sh     # full pytest + smoke + live docker
```

**Do not** run `pytest`, `pip install -e ".[dev]"`, or `scripts/integration-smoke.sh` directly on the host.

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
- **`command not found: cli`** — run `./scripts/install.sh`, then open a new terminal or `source ~/.zprofile`.
- **`cli git review` fails** — full review calls `./scripts/test-unit.sh`; use `--quick` for shell syntax only.
