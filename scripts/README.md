# scripts/

Shell-only entry points. Python code lives under [`src/`](../src/) and [`tests/`](../tests/).

| Script / directory | Purpose |
| --- | --- |
| `pypi/` | Local install + release (`install.sh`, `build.sh`, `upload.sh`, `test.sh`, `release.sh`, `publish.sh`) |
| `test/` | Docker test harness (`unit.sh`, `integration.sh`, `smoke.sh`, `tags.sh`, `all.sh`) |
| `docker/` | Image build, in-container runners, CI bootstrap (`bootstrap.sh`) |
| `drive/` | Drive sync scripts (`status.sh`, `ingest.sh`, …) |
| `git/`, `chrome/`, `notion/`, `gh/` | CLI shell shortcuts |

Integration check runners (Python): [`tests/integration/`](../tests/integration/).
