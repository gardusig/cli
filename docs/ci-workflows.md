# Gardusig CI/CD — Docker pipeline

CI and Docker run **outside this repository** (central DevOps). This repo has no `Dockerfile`, `scripts/docker/`, or `.github/workflows/`.

## Triggers

| Event | Pipeline |
| --- | --- |
| Pull request | Unit → integration → regression → PyPI smoke |
| Tag `v*` | Build wheel/sdist → publish to PyPI |

## Local development

Use a normal Python venv for day-to-day work. Docker-based verification mirrors what central CI runs; ask maintainers for the current `docker build` invocation.

## Timeouts

| Gate | Default |
|------|---------|
| Unit | 10 min |
| Integration | 20 min |
| Regression | 15 min |

See [setup.md](setup.md) and [docker.md](docker.md) for install and harness details.
