# Gardusig CI/CD — Docker pipeline

CI and Docker workflow definitions run **outside this repository** (central DevOps).
This repo has no root `Dockerfile` or `.github/workflows/`; command behavior lives in Python services.

## Triggers

| Event | Pipeline |
| --- | --- |
| Pull request | Unit → integration → regression → PyPI smoke |
| Tag `v*` | Build wheel/sdist → publish to PyPI |

## Local development

Use a normal Python venv for day-to-day work. Docker-based verification mirrors what central CI runs; ask maintainers for the current `docker build` invocation.

## Selective test contract

`python-cli` does not own GitHub Actions workflow YAML. The central
`gardusig/github-pipelines` repo owns pull-request matrices, Dockerfiles,
schedules, branch protection, and labels.

This repo exposes the stable command contract that those pipelines consume:

```bash
cli test packages resolve --base "$BASE_SHA" --head "$HEAD_SHA" --format json
cli test packages run gh --dry-run --format json
cli test packages run gh --no-unit --dry-run --format json
cli test packages suite --format json
cli pypi version check --base origin/main
cli pypi upload --testpypi --skip-existing --yes
cli release main --yes
```

Per-package local scripts (delegate to `cli test packages run`):

```bash
scripts/test/gh.sh --dry-run
scripts/test/git.sh --no-unit --dry-run
scripts/test/pypi.sh --dry-run
scripts/test/all.sh
```

### Package matrix

| Package | Unit tests | Integration leg |
| --- | --- | --- |
| `git` | `tests/git/` | `check_package_integration.py --package git` (workflows + git endpoints) |
| `gh` | `tests/gh/` | package integration + filtered `cli_api_checks` |
| `notion` / `drive` / `chrome` | `tests/{pkg}/` | package integration + API workspace |
| `docker` | `tests/docker/` | package integration + `check_docker_commands.py` |
| `contest` | `tests/contest/` | package integration |
| `project` | `tests/project/` | package integration |
| `pypi` | `tests/pypi/` | package integration + `pypi --help` |
| `cli` (broad) | `tests/cli/` | full `check_public_commands.py` via core gates |

`resolve` returns package names, focused unit paths, integration checks, broad
fallback flags, token-cost flags, and recommended stable check names. If
`full_suite=true`, pipelines should run the full-suite contract instead of only
selected package legs.

`run PACKAGE --no-unit --dry-run` is the package-filtered integration contract
for Docker jobs. Integration legs use `tests/integration/check_package_integration.py`
for API and workflow packages instead of the monolithic `check_api_integration.py`.

### Nightly full suite (#85)

`suite` is the nightly/manual full-suite safety net: core gates, every package
unit/integration command, plus optional `check_docker_commands.py --live`.

```bash
cli test packages suite --format json   # plan legs
cli test packages suite --dry-run       # print commands only
```

`github-pipelines` should schedule `python-cli-test-nightly.yml` on `main` (cron +
`workflow_dispatch`) and honor label `ci:full` on PRs for the same contract.

### PR CI flow (github-pipelines)

1. `cli test packages resolve --base "$BASE" --head "$HEAD" --format json`
2. If `full_suite` → run `cli test packages suite` (+ execute live docker leg)
3. Else matrix `package_names` → `cli test packages run "$pkg" --no-unit` per cell
4. Always run core gates: `check_integration_coverage.py`, `check_public_commands.py`
5. Label `ci:full` or merge queue → full suite

PyPI publishing uses the same split: this repo owns `cli pypi ...` and
`cli release ...`; `github-pipelines` owns workflow YAML, Docker images,
trusted publishing/OIDC or token wiring, schedules, and branch protection.

## Timeouts

| Gate | Default |
|------|---------|
| Unit | 10 min |
| Integration | 20 min |
| Regression | 15 min |

See [setup.md](setup.md) and [docker.md](docker.md) for install and harness details.
