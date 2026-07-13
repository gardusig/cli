# Docker stages

Each app repository owns a multi-stage `Dockerfile` at the repo root. Stages are run with `docker build --target <stage> -f Dockerfile .` from that repository.

## `gardusig/cli` (this repo)

Root `Dockerfile` stages:

| Target | Purpose |
| --- | --- |
| `version-check`, `unit-test`, `testpypi`, `testpypi-consumer` | PR pipeline |
| `pypi`, `runtime` | Release (PyPI publish + lean runtime image) |

## Exceptions (other repos)

| Repo | Dockerfile path | Notes |
| --- | --- | --- |
| `gardusig/tex` | `docker/Dockerfile` | LaTeX + Pages publish layout |
| `gardusig/wiki` | `Dockerfile` + `docker/mermaid.Dockerfile` | Separate Mermaid validation image |

## Common stage order (app repos)

1. `lint` — `cli lint repo /workspace`
2. `repo-hygiene` — `cli structure check` with optional `HYGIENE_POLICY_JSON`
3. Repo-specific gates (`unit-test`, `integration-test`, `build`, `latex`, …)

## Local example (`gardusig/cli`)

```bash
export BASE_VERSION="$(bash scripts/pull-request/host-last-published-version.sh)"
docker build --target version-check --build-arg "BASE_VERSION=${BASE_VERSION}" .
docker build --target unit-test .
```

## PR publish stages (`gardusig/cli`)

| Stage | Purpose |
| --- | --- |
| `version-check` / `unit-test` | PR gate |
| `testpypi` / `testpypi-consumer` | TestPyPI publish + install smoke |

## Release stages (`gardusig/cli`)

| Stage | Purpose |
| --- | --- |
| `pypi` | Production PyPI publish |
| `runtime` | Lean image from PyPI (`gardusig-cli==$VERSION`) |
