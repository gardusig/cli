# Setup (macOS)

## Install vs verify

| Lane | Purpose | Entry |
| --- | --- | --- |
| **Install** | Run `shuttle` on macOS | `./scripts/bootstrap.sh` or `./scripts/install.sh` |
| **Verify** | Unit + integration gates (CI-equivalent) | `./scripts/test-unit.sh`, `./scripts/test-integration.sh` |

Local `.venv` gets **runtime** dependencies only. Pytest, coverage, and smoke scripts run **inside** Docker (`shuttle-cli:unit` / `shuttle-cli:integration`) so checks never mutate your checkout.

## Requirements

- Python **3.12+** (local CLI via `bootstrap.sh` / `install.sh`)
- `git` on PATH
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) for verification (`shuttle-cli:dev` Linux image)
- Optional: `gh` for GitHub (used by cursor-skills, not shuttle-cli)

## Local install

```bash
git clone https://github.com/gardusig/shuttle-cli.git
cd shuttle-cli
./scripts/bootstrap.sh
source .venv/bin/activate
python -m shuttle --help
```

Manual venv (runtime only): `pip install -r requirements.txt` then `pip install -e .`  
Host dev tools (not needed for Docker verify): `pip install -r requirements-dev.txt` or `pip install -e ".[dev]"`.

## User install

```bash
./scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
shuttle --version
```

## Verify (Docker)

Same scripts as GitHub Actions. See [docker.md](docker.md).

```bash
./scripts/docker/build-image.sh   # optional; auto-builds on first run
./scripts/test-unit.sh            # unit gate (≥80% coverage)
./scripts/test-integration.sh     # full pytest + smoke + live docker
```

**Do not** run `pytest`, `pip install -e ".[dev]"`, or `scripts/integration-smoke.sh` directly on the host.

## After install

1. `cd` into a git repository for `shuttle git` commands.
2. Optional: edit `config/config.yaml` → `backup.repositories` for `shuttle drive status` / `drive ingest`.
3. Chrome `bookmarks deploy` (local → browser) needs a prior `bookmarks ingest` into your configured `chrome.bookmarks_file`.

See [configuration.md](configuration.md) and README **Configuration**.

## Troubleshooting

- **`git` not in a repository** — run commands from a git worktree root.
- **Refusing to push** — pass `--yes` to confirm: `shuttle git push --yes`.
- **Dirty tree on `main`** — pass `--yes` to destructive align/reset commands.
- **`shuttle git start` deleted my files** — use `--no-prep` to branch in place; default `start` aligns main first.
- **`docker is not installed`** when testing — install Docker Desktop; verification does not use host Python.
- **`shuttle git review` fails** — full review calls `./scripts/test-unit.sh`; use `--quick` for shell syntax only.
