# Docker stages

Each app repository owns a multi-stage `Dockerfile` at the repo root. Stages are run with `docker build --target <stage> -f Dockerfile .` from that repository.

Hub-only images remain under `gardusig/cli/docker/`:

| Image | Path | Purpose |
| --- | --- | --- |
| Operator runner | `docker/operator.dockerfile` | `ghcr.io/gardusig/operator-runner` |
| CLI base | `docker/cli-base.dockerfile` | Lean jobs that run published `gardusig-cli` |

## Exceptions

| Repo | Dockerfile path | Notes |
| --- | --- | --- |
| `gardusig/tex` | `docker/Dockerfile` | LaTeX + Pages publish layout |
| `gardusig/wiki` | `Dockerfile` + `docker/mermaid.Dockerfile` | Separate Mermaid validation image |

## Common stage order

1. `lint` — `cli lint repo /workspace`
2. `repo-hygiene` — `cli structure check` with optional `HYGIENE_POLICY_JSON`
3. Repo-specific gates (`unit-test`, `integration-test`, `build`, `latex`, …)

## `gardusig/cli` example

```bash
docker build --target lint -f Dockerfile .
docker build --target repo-hygiene -f Dockerfile .
docker build --target unit-test -f Dockerfile .
```

| Stage | Purpose |
| --- | --- |
| `lint` | Markdown + mermaid validation |
| `repo-hygiene` | Layout policy from `.github/pull-request.yaml` |
| `version-check` | `cli pypi version check` |
| `core-gates` | Integration coverage + public command surface |
| `package-unit` / `package-integration` | Selective package legs |
| `unit-test` / `integration-test` | Full suite |
| `pypi-test` / `release` | TestPyPI / PyPI publish |
