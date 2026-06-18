# scripts/

Shell-only entry points. Python code lives under [`shuttle/`](../shuttle/) and [`tests/`](../tests/).

| Script / directory | Purpose |
| --- | --- |
| `bootstrap.sh`, `install.sh` | Host setup |
| `test-unit.sh`, `test-integration.sh` | Docker test harness wrappers |
| `integration-smoke.sh` | Integration smoke (container only) |
| `backup-status.sh` | `shuttle drive status` shortcut |
| `docker/` | Image build + in-container unit/integration runners |
| `git/`, `chrome/`, `notion/`, `drive/` | CLI shell shortcuts |

Integration check runners (Python): [`tests/integration/`](../tests/integration/).
