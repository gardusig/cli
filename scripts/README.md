# scripts/

Shell-only entry points. Python code lives under [`gardusig_cli/`](../gardusig_cli/) and [`tests/`](../tests/).

| Script / directory | Purpose |
| --- | --- |
| `install.sh`, `bootstrap.sh` | User install (PyPI) vs contributor venv (Docker/CI only) |
| `test/` | Docker test harness (`unit.sh`, `integration.sh`, `smoke.sh`) |
| `pypi/` | PyPI build, test, release (`build.sh`, `upload.sh`, `test.sh`, `release.sh`, `publish.sh`) |
| `drive/` | Drive sync scripts (`status.sh`, `ingest.sh`, …) |
| `docker/` | Image build + in-container unit/integration runners |
| `git/`, `chrome/`, `notion/`, `gh/` | CLI shell shortcuts |

Integration check runners (Python): [`tests/integration/`](../tests/integration/).
