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

`resolve` returns package names, focused unit paths, integration checks, broad
fallback flags, token-cost flags, and recommended stable check names. If
`full_suite=true`, pipelines should run the full-suite contract instead of only
selected package legs.

`run PACKAGE --no-unit --dry-run` is the package-filtered integration contract
for Docker jobs. `suite` is the nightly/manual full-suite safety net: it expands
the core gates plus every package unit/integration command, while
`github-pipelines` decides scheduling and job fan-out.

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
