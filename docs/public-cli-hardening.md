# Public CLI Hardening Review

Epic [#57](https://github.com/gardusig/python-cli/issues/57) reviewed the public `cli` command surface after product epics landed. The console command is `cli`; the package is `gardusig-cli`.

**Status (PR #88):** integration coverage gate **150/150**; child matrix #58–#65 verified; meta coverage tests aligned with `ok_exempt` deferred rows (`chrome photos` / #50).

**Merge readiness (PR #88, 2026-07-06):** `gardusig-cli` **1.0.2**; integration gate **150/150**; verification **511** tests green (40 meta/pipeline + 471 package); `cli pypi version check` passes; selective resolve E2E against `github-pipelines` python-cli.yaml.

**Epic 06 status:** Pre-merge complete on branch. [github-pipelines PR #2](https://github.com/gardusig/github-pipelines/pull/2) merged; PR #88 CI dispatched. Post-merge: `docs/release.md` § Post-merge release.

## Current Matrix

| Issue | Surface | Status | Notes |
| --- | --- | --- | --- |
| [#58](https://github.com/gardusig/python-cli/issues/58) | `cli git` | **Pass** | `public_endpoints` git subcommands, remote mocks (`git_mocks.py`), `docs/git.md`, push warnings + `--format json`, workflow push scenarios. Epic 09 (#67) closes branch-policy edge cases. |
| [#59](https://github.com/gardusig/python-cli/issues/59) | `cli drive` | **Pass** | Epic 04: providers, partial failure, `--dry-run`/JSON, Proton deferral, `cli_api_checks`. Close #4 epic. |
| [#60](https://github.com/gardusig/python-cli/issues/60) | `cli notion` | **Pass** | Epic 03: pairs, repo-derived `link`, partial failure, `cli tasks` shortcuts, `tests/notion/`. Close #2 epic. |
| [#61](https://github.com/gardusig/python-cli/issues/61) | `cli chrome` | **Pass** | Epic 02: merge/snapshot/`--profile`, `docs/chrome.md`, Photos deferral (#50). #48 (bookmarks update script) superseded by `cli chrome bookmarks merge|snapshot`. Close #24 epic. |
| [#62](https://github.com/gardusig/python-cli/issues/62) | `cli docker` | **Pass** | JSON + filter integration smoke; write `--format json`; `check_docker_commands.py` mocked + `--live` contract in `docs/docker.md`. |
| [#63](https://github.com/gardusig/python-cli/issues/63) | `cli gh` / `cli project` | **Pass** | GH CRUD + policy in `cli_api_checks`; API-transport smoke (`gh issue list api`, `gh pr checks api`, `gh project view api`, `gh project item add api`, `gh transport refuse`); top-level `project_integration` checks for list/spawn/pairs/deploy/link. |
| [#64](https://github.com/gardusig/python-cli/issues/64) | `cli contest` | **Pass** | `contest_integration` + Codeforces walkthrough in `docs/contest.md`. Close #54 epic. |
| [#65](https://github.com/gardusig/python-cli/issues/65) | `cli links`, `restore`, aliases | **Pass** | `catalog.py` indexes visible groups; `restore` placeholder stable; hidden aliases intentional. |
| [#51](https://github.com/gardusig/python-cli/issues/51) | Output organization | **Closed policy** | JSON-first for agents; Rich tables where already useful; no broad theme rewrite. |

## Output policy (#51)

- Agent-facing commands expose `--format json` where structured output helps automation (`gh`, `docker`, `project`, `git push`, many `git` reads).
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
uv run pytest tests/meta/test_integration_coverage_gate.py tests/meta/test_utils_helpers.py -q
uv run python tests/integration/check_integration_coverage.py
uv run pytest tests/integration/check_integration_coverage.py -q
uv run pytest tests/project/test_integration_checks.py tests/contest/test_integration_checks.py -q
uv run pytest tests/cli/test_links.py tests/cli/test_api_integration.py -q
uv run pytest tests/git/ tests/gh/ tests/docker/ tests/chrome/ tests/notion/ tests/drive/ tests/contest/ -q
```

Docker integration (full public command matrix):

```bash
# In github-pipelines docker integration job
python tests/integration/check_public_commands.py
python tests/integration/check_api_integration.py
```

## Closure recommendations

- Close **#57** when [PR #88](https://github.com/gardusig/python-cli/pull/88) merges with the verification block above green.
- Close child issues **#58–#65** and output policy **#51** (documented above; no theme rewrite).
- Close product epics **#2**, **#4**, **#24**, **#54**, **#66–#70** when PR #88 merges with evidence.
- Close **#52** and Epic **09** (#67) — push warnings, detached-HEAD refusal, and `git push --format json` shipped on PR #88.
- Close **#48** — superseded by `cli chrome bookmarks merge` and `snapshot` (see `docs/chrome.md`).
- Epic **00-infra** ([#81](https://github.com/gardusig/python-cli/issues/81)–[#85](https://github.com/gardusig/python-cli/issues/85)): selective CI contract shipped (`pipeline_selective`, `cli pipeline config resolve --app-src`); **#83–#85** close when `github-pipelines` PR adopts selective yaml + nightly (`python-cli-test-nightly.yml`).
- Leave **#50** (Chrome Photos) open for future work.
- Retarget only genuinely new automation to the owning product epic, not Epic 07.
- **Epic 06 (PyPI release):** PR #88 bumps `gardusig-cli` to `1.0.2` for `cli pypi version check`; post-merge run TestPyPI then `cli release main --yes` (see `docs/release.md`).

## Next epic: hub operator

After PR #88 merges and ships **1.0.2**, track **`epic:hub-operator`** ([`docs/hub-operator.md`](hub-operator.md)):

- Phase A (docs + pack tests) lands on PR #88.
- Phase B (`ghcr.io/gardusig/operator-runner`) lands in `github-pipelines`.
- Phases C–E: reusable `workflow_call` lanes (`operator-test` shipped) + `workflow_dispatch` orchestrator.
