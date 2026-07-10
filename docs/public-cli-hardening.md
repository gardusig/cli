# Public CLI hardening

Checklist for the public `cli` command surface. Console command: **`cli`**; PyPI package: **`gardusig-cli`**.

## Registry contracts

| File | Role |
| --- | --- |
| [`src/cli.py`](../src/cli.py) | Visible and hidden command groups |
| [`src/integration/public_endpoints.py`](../src/integration/public_endpoints.py) | Top-level and git/pypi endpoint smoke |
| [`src/integration/cli_api_checks.py`](../src/integration/cli_api_checks.py) | Mocked gh/notion/drive/chrome API checks |
| [`src/integration/project_integration.py`](../src/integration/project_integration.py) | Mocked top-level `cli project` checks |
| [`src/integration/contest_integration.py`](../src/integration/contest_integration.py) | Mocked `cli contest validate` checks |
| [`src/integration/docker_integration.py`](../src/integration/docker_integration.py) | Mocked `cli docker` checks |
| [`src/integration/integration_coverage.py`](../src/integration/integration_coverage.py) | ok/fail inventory gate |
| [`src/services/test_packages.py`](../src/services/test_packages.py) | Changed-path → focused tests |
| [`src/utils/catalog.py`](../src/utils/catalog.py) | `cli links` discoverability |

## Output policy

- Agent-facing commands expose `--format json` where structured output helps automation (`gh`, `docker`, `project`, `git push`, many `git` reads).
- Human-readable Rich tables and color remain on commands that already use them.
- Errors use `[red]error:[/red]` or actionable `RuntimeError` messages (missing tokens, manifests, config paths).
- Write gates print `Refusing write in non-interactive mode` unless `--yes` is passed.

## Verification

```bash
uv run pytest tests/meta/test_integration_coverage_gate.py tests/meta/test_utils_helpers.py -q
uv run python tests/integration/check_integration_coverage.py
uv run pytest tests/integration/check_integration_coverage.py -q
uv run pytest tests/project/test_integration_checks.py tests/contest/test_integration_checks.py -q
uv run pytest tests/cli/test_links.py tests/cli/test_api_integration.py -q
uv run pytest tests/git/ tests/gh/ tests/docker/ tests/chrome/ tests/notion/ tests/drive/ tests/contest/ -q
```

Docker integration (full public command matrix):

```bash
docker build -f .github/Dockerfile --target integration-test .
python tests/integration/check_public_commands.py
python tests/integration/check_api_integration.py
```

## CI ownership

This repository owns application code, docs, [`.github/Dockerfile`](../.github/Dockerfile), `scripts/ci/*.sh`, and [`.github/workflows/`](../.github/workflows/) for pull-request and tag release pipelines. Optional hub routers live in [`gardusig/cli`](https://github.com/gardusig/cli) for broader monorepo CI.
