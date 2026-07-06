# Per-package test scripts (Epic 00-infra #82)

Thin wrappers around `cli test packages run`. Each script sets `CLI_CONFIG_DIR=config/ci`
and delegates to the registry in `src/services/test_packages.py`.

## Nine-script policy

Shell scripts exist only for packages that own a **Docker integration leg** in selective
CI (`check_package_integration.py`). All other packages use the CLI directly:

```bash
cli test packages run lint --dry-run
cli test packages run deploy --dry-run
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

`all.sh` prints the **full-suite** contract (`cli test packages suite`) for nightly /
`ci:full` safety-net runs.

## Examples

```bash
scripts/test/gh.sh --dry-run
scripts/test/gh.sh --no-unit --dry-run    # integration leg only (pipeline shape)
scripts/test/all.sh --format json
```

See [docs/ci-workflows.md](../../docs/ci-workflows.md) and [tests/README.md](../../tests/README.md).
