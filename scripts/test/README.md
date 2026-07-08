# Per-package test scripts (Epic 00-infra #82)

Thin wrappers around **raw `pytest`** paths (no `cli test packages run`, no `python3 -m src`).
Shared helpers live in `_common.sh`.

## Nine-script policy

Shell scripts exist only for packages that own a **Docker integration leg** in selective
CI (`check_package_integration.py`). All other packages use pytest or the CLI locally:

```bash
uv run pytest tests/lint/ -q
cli test packages run deploy --dry-run   # local only; not used in scripts/
```

| Script | Package | Integration leg |
| --- | --- | --- |
| `gh.sh` | `gh` | GitHub API + workflow mocks |
| `git.sh` | `git` | Git endpoints + workflow scenarios |
| `notion.sh` | `notion` | Notion API workspace |
| `drive.sh` | `drive` | Drive API workspace |
| `chrome.sh` | `chrome` | Chrome bookmarks workspace |
| `docker.sh` | `docker` | `check_docker_commands.py` |
| `contest.sh` | `contest` | Contest validate integration |
| `project.sh` | `project` | Top-level `cli project` checks |
| `pypi.sh` | `pypi` | PyPI package integration |

`all.sh` documents the **full-suite** contract (`scripts/ci/unit-test.sh` +
`scripts/ci/integration-test.sh`) for nightly / `ci:full` runs.

## Examples

```bash
scripts/test/gh.sh --dry-run
scripts/test/gh.sh --no-unit --dry-run    # integration leg only (pipeline shape)
scripts/test/all.sh --format json
```

See [docs/ci-workflows.md](../../docs/ci-workflows.md) and [tests/README.md](../../tests/README.md).
