# Public CLI Hardening Review

Epic [#57](https://github.com/gardusig/python-cli/issues/57) reviewed the public `cli` command surface after product epics landed. The console command is `cli`; the package is `gardusig-cli`.

**Status (`main`, post-#88):** integration coverage gate **154/154**+; child matrix #58–#65 verified; `chrome photos` ingest shipped on PR #96 ([#50](https://github.com/gardusig/python-cli/issues/50)).

**Shipped on `main`:** [#88](https://github.com/gardusig/python-cli/pull/88) (language-first CLI, epics 07–12, 00-infra) and [#95](https://github.com/gardusig/python-cli/pull/95) (`cli ship`). `gardusig-cli` **1.0.3** on `main`; dev gate **1.0.4** on release PR.

**Epic 06d status:** PR #88 merged; PyPI release **1.0.3** pending `cli release main --yes`; pipelines `BASE_VERSION` → **1.0.3**; backlog closure in progress. See § Epic 06d below.

## Current Matrix

| Issue | Surface | Status | Notes |
| --- | --- | --- | --- |
| [#58](https://github.com/gardusig/python-cli/issues/58) | `cli git` | **Pass** | `public_endpoints` git subcommands, remote mocks (`git_mocks.py`), `docs/git.md`, push warnings + `--format json`, workflow push scenarios. Epic 09 (#67) closes branch-policy edge cases. |
| [#59](https://github.com/gardusig/python-cli/issues/59) | `cli drive` | **Pass** | Epic 04: providers, partial failure, `--dry-run`/JSON, `sync --status`, Proton deferral, `cli_api_checks`. #30 closes on PR #96. |
| [#60](https://github.com/gardusig/python-cli/issues/60) | `cli notion` | **Pass** | Epic 03: pairs, repo-derived `link`, partial failure, `cli tasks` shortcuts, `tests/notion/`. Close #2 epic. |
| [#61](https://github.com/gardusig/python-cli/issues/61) | `cli chrome` | **Pass** | Epic 02: bookmarks + Takeout photos ingest (`cli chrome photos`), `docs/chrome.md`. #48 superseded by `merge` + `snapshot`. |
| [#62](https://github.com/gardusig/python-cli/issues/62) | `cli docker` | **Pass** | JSON + filter integration smoke; write `--format json`; `check_docker_commands.py` mocked + `--live` contract in `docs/docker.md`. |
| [#63](https://github.com/gardusig/python-cli/issues/63) | `cli gh` / `cli project` | **Pass** | GH CRUD + policy in `cli_api_checks`; API-transport smoke (`gh issue list api`, `gh issue context api`, `gh pr checks api`, `gh pr shortcut api`, `gh project view api`, `gh project item add api`, `gh transport refuse`); top-level `project_integration` checks for list/spawn/pairs/deploy/link. |
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
- Epic **00-infra** ([#81](https://github.com/gardusig/python-cli/issues/81)–[#85](https://github.com/gardusig/python-cli/issues/85)): contract on PR #88; [pipelines PR #20](https://github.com/gardusig/github-pipelines/pull/20) for `ci:full` + nightly; close #81–#82 on merge, #83–#85 after pipelines merge + green nightly.
- Epic **08-projects** ([#66](https://github.com/gardusig/python-cli/issues/66)–[#75](https://github.com/gardusig/python-cli/issues/75)): close when PR #88 merges — evidence in `docs/project.md` § Epic 08 closure; hub `project-recurrence.yml` ([pipelines #16](https://github.com/gardusig/github-pipelines/pull/16)).
- Close **#50** when PR #96 merges with photos ingest verification green.
- Close **#30** when PR #96 merges with drive sync verification green (`tests/drive/`, `tests/pack/test_drive_sync_epic.py`).
- Close **#12**, **#13**, **#29**, **#14** (deferred), **#15** when PR #96 merges with provider/automation evidence (`tests/pack/test_drive_providers_epic.py`).
- Close **#20**, **#21**, **#22**, **#23**, **#31** when PR #96 merges with Notion evidence (`tests/notion/`, `tests/pack/test_notion_epic.py`).
- Close **#27**, **#28** when PR #96 merges with Chrome bookmarks evidence (`tests/pack/test_chrome_bookmarks_epic.py`).
- Retarget only genuinely new automation to the owning product epic, not Epic 07.
- **Epic 06 (PyPI release):** PR #88 bumps `gardusig-cli` to `1.0.3` for `cli pypi version check`; post-merge run TestPyPI then `cli release main --yes` (see `docs/release.md`).

## Epic 06d — Release and backlog closure

**Current gate:** release **1.0.3** from `main` (pre-1.0.4 bump), pin hub CI, close shipped issues.

| Step | Action | Status |
| --- | --- | --- |
| 1 | Merge PR #88 + #95 | **Done** |
| 2 | `cli release main --yes` → PyPI **1.0.3** | Maintainer (`PYPI_API_TOKEN`) |
| 3 | Bump `github-pipelines` `BASE_VERSION` to **1.0.3** | PR with this epic |
| 4 | Bump `main` dev gate to **1.0.4** | PR with this epic |
| 5 | Rebuild `ghcr.io/gardusig/operator-runner` with `CLI_VERSION=1.0.3` | After PyPI ship |
| 6 | Close #57–#85, #2, #4, #24, #54, #66–#70 per § Closure recommendations | PR / maintainer |

Evidence: [`docs/release.md`](release.md) § Post-merge release; pack smoke `tests/pack/test_release_epic.py`.

**Shipped on `main` (close in 06d):** Epics **08**, **09**, **10**, **11**, **12**, **hub-operator**, **00-infra** — see [`docs/project.md`](project.md), [`docs/gh.md`](gh.md), [`docs/docker.md`](docker.md), [`docs/ci-workflows.md`](ci-workflows.md), [`docs/hub-operator.md`](hub-operator.md).

## Epic 02 — Chrome Photos (#50) on PR #96

**Status:** `cli chrome photos list|ingest|status` shipped (Takeout file ingest). Closes #50 when PR merges.

See [`docs/chrome.md`](chrome.md#google-photos).

## Epic 04 — Drive sync (#30) on PR #96

**Status:** `cli drive sync` hardening shipped — dry-run ingest+deploy plan, `--status` preflight, `--strict/--no-strict`, integration checks (**156/156**), pack smoke `tests/pack/test_drive_sync_epic.py`. Closes #30 when PR merges.

Primary workflow:

```bash
cli drive sync --status --format json
cli drive sync --dry-run --format json
cli drive sync
```

See [`docs/drive.md`](drive.md) § Local workflow catalog.

## Epic 04d — Drive providers & automation (#12–#15, #29) on PR #96

**Status:** close-as-shipped evidence on this PR (merge closes children when verified green).

| Issue | Evidence |
| --- | --- |
| **#12** Google Drive | `src/providers/google_drive.py`, `tests/providers/test_google_drive.py` |
| **#13** OneDrive | `src/providers/onedrive.py`, `tests/providers/test_onedrive.py` |
| **#14** Proton | Deferred — `ProtonDriveUnsupportedError`, `docs/drive.md` § Proton Drive |
| **#29** Download | `cli drive download`, integration checks, `docs/drive.md` § Download semantics |
| **#15** Automation | `docs/drive.md` § Tag backup automation + failure modes; hub owns launchd |

Pack smoke: `tests/pack/test_drive_providers_epic.py`.

```bash
uv run pytest tests/providers/ tests/pack/test_drive_providers_epic.py -q
```

## Epic 03d — Notion backlog closure (#20–#23, #31) on PR #96

**Status:** close-as-shipped evidence on this PR (merge closes children when verified green). Parent **#2** already closed.

| Issue | Evidence |
| --- | --- |
| **#20** Ingest | `export_tasks` in `notion_sync.py`, `cli notion ingest`, integration check |
| **#21** Deploy | `import_tasks`, `cli notion deploy`, partial-failure exit codes |
| **#22** Cleanup | `cleanup_board`, `cli notion cleanup` |
| **#23** Auth/mapping | `NOTION_TOKEN`, `notion.properties` in `docs/notion.md`, `require_notion_token` |
| **#31** Sync | `cli notion sync` Phase 1/2, `cli tasks` shortcuts in `docs/notion.md` |

Pack smoke: `tests/pack/test_notion_epic.py`. Matrix **#60 Pass**.

```bash
uv run pytest tests/notion/ tests/pack/test_notion_epic.py -q
uv run python tests/integration/check_integration_coverage.py
```

## Epic 02d — Chrome bookmarks backlog (#27, #28) on PR #96

**Status:** close-as-shipped evidence on this PR (merge closes last open product children). Parent **#24** already closed.

| Issue | Evidence |
| --- | --- |
| **#27** Workflow docs | `docs/chrome.md`, `docs/bookmarks.md`, env vars, pipelines boundary (no repo scripts) |
| **#28** Snapshots + profiles | `cli chrome bookmarks snapshot`, `chrome.profiles`, `snapshot_retention` |

Pack smoke: `tests/pack/test_chrome_bookmarks_epic.py`.

```bash
uv run pytest tests/chrome/ tests/pack/test_chrome_bookmarks_epic.py -q
```
