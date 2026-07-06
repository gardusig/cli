# Public CLI Hardening Review

Epic [#57](https://github.com/gardusig/python-cli/issues/57) reviewed the public `cli` command surface after product epics landed. The console command is `cli`; the package is `gardusig-cli`.

## Current Matrix

| Issue | Surface | Status | Notes |
| --- | --- | --- | --- |
| [#58](https://github.com/gardusig/python-cli/issues/58) | `cli git` | **Pass** | `public_endpoints` git subcommands, remote mocks (`git_mocks.py`), `docs/git.md`, `cli links` entries. Residual branch-policy work tracked in Epic 09 (#67). |
| [#59](https://github.com/gardusig/python-cli/issues/59) | `cli drive` | **Pass** | Epic 04: providers, partial failure, `--dry-run`/JSON, Proton deferral, `cli_api_checks`. Close #4 epic. |
| [#60](https://github.com/gardusig/python-cli/issues/60) | `cli notion` | **Pass** | Epic 03: pairs, repo-derived `link`, partial failure, `cli tasks` shortcuts, `tests/notion/`. Close #2 epic. |
| [#61](https://github.com/gardusig/python-cli/issues/61) | `cli chrome` | **Pass** | Epic 02: merge/snapshot/`--profile`, `docs/chrome.md`, Photos deferral (#50). Close #24 epic. |
| [#62](https://github.com/gardusig/python-cli/issues/62) | `cli docker` | **Pass** | JSON + filter integration smoke; write `--format json`; `check_docker_commands.py` mocked + `--live` contract in `docs/docker.md`. |
| [#63](https://github.com/gardusig/python-cli/issues/63) | `cli gh` / `cli project` | **Pass** | GH CRUD + policy in `cli_api_checks`; API-transport smoke (`gh issue list api`, `gh pr checks api`, `gh project view api`, `gh project item add api`, `gh transport refuse`); top-level `project_integration` checks for list/spawn/pairs/deploy/link. |
| [#64](https://github.com/gardusig/python-cli/issues/64) | `cli contest` | **Pass** | `contest_integration` + Codeforces walkthrough in `docs/contest.md`. Close #54 epic. |
| [#65](https://github.com/gardusig/python-cli/issues/65) | `cli links`, `restore`, aliases | **Pass** | `catalog.py` indexes visible groups; `restore` placeholder stable; hidden aliases intentional. |
| [#51](https://github.com/gardusig/python-cli/issues/51) | Output organization | **Closed policy** | JSON-first for agents; Rich tables where already useful; no broad theme rewrite. |

## Output policy (#51)

- Agent-facing commands expose `--format json` where structured output helps automation (`gh`, `docker`, `project`, many `git` reads).
- Human-readable Rich tables and color remain on commands that already use them; do not introduce a global theme layer.
- Errors use `[red]error:[/red]` or actionable `RuntimeError` messages (missing tokens, manifests, config paths).
- Write gates print `Refusing write in non-interactive mode` unless `--yes` is passed.

## Registry contracts

| File | Role |
| --- | --- |
| [`src/cli.py`](src/cli.py) | Visible and hidden command groups |
| [`src/integration/public_endpoints.py`](src/integration/public_endpoints.py) | Top-level and git/pypi endpoint smoke |
| [`src/integration/cli_api_checks.py`](src/integration/cli_api_checks.py) | Mocked gh/notion/drive/chrome API checks |
| [`src/integration/project_integration.py`](src/integration/project_integration.py) | Mocked top-level `cli project` checks |
| [`src/integration/contest_integration.py`](src/integration/contest_integration.py) | Mocked `cli contest validate` checks |
| [`src/integration/docker_integration.py`](src/integration/docker_integration.py) | Mocked `cli docker` checks |
| [`src/integration/integration_coverage.py`](src/integration/integration_coverage.py) | ok/fail inventory gate |
| [`src/services/test_packages.py`](src/services/test_packages.py) | Changed-path → focused tests |
| [`src/utils/catalog.py`](src/utils/catalog.py) | `cli links` discoverability |

`gardusig/github-pipelines` owns workflow YAML, Dockerfiles, schedules, and job graphs.

## Verification

```bash
uv run pytest tests/integration/check_integration_coverage.py -q
uv run pytest tests/project/test_integration_checks.py tests/contest/test_integration_checks.py -q
uv run pytest tests/cli/test_links.py tests/cli/test_api_integration.py -q
uv run pytest tests/notion/ tests/drive/ tests/chrome/ tests/contest/ -q
```

Docker integration (full public command matrix):

```bash
# In github-pipelines docker integration job
python tests/integration/check_public_commands.py
python tests/integration/check_api_integration.py
```

## Closure recommendations

- Close **#57** when verification passes and child issues #58–#65 + #51 are closed.
- Close product epics **#2**, **#4**, **#24**, **#54** with this hardening PR as evidence.
- Leave **#50** (Chrome Photos) and **#67–#70** feature epics open for future work.
- Retarget only genuinely new automation to the owning product epic, not Epic 07.
