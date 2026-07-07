# Repository Contract

This is the canonical repository contract for the gardusig repositories.

## Active Decisions

- `python-cli` owns validation logic and developer commands.
- `github-pipelines` owns reusable GitHub Actions routers, hub-only images (`docker/operator.dockerfile`, `docker/cli-base.dockerfile`), and schedules.
- App repositories keep application code plus:
  - `.github/workflows/pull-request.yml` — thin caller into the central router
  - `.github/workflows/release.yml` — optional tag publish workflow (language libraries)
  - `.github/pull-request.yaml` — per-repo job graph and hygiene policy
  - `Dockerfile` — multi-stage CI image (repo root; `docker/Dockerfile` only for complex layouts such as `tex`)
- App repositories must not contain extra workflow files or CI shell scripts. Docker stages live in each repo's `Dockerfile`.
- Setup and validation are Docker-first. Run individual stages instead of installing dependencies locally.

## Docker Stage Model

Every repo `Dockerfile` follows the same stage order:

1. `lint` — `cli lint repo /workspace` inside Docker; it runs lint for each language present in that repo
2. `repo-hygiene` — layout, folder depth (up to policy `max_depth`), language allowlists, and forbidden orchestration artifacts
3. Repo-specific stages — `unit-test`, `integration-test`, `build`, `validate`, etc.

Example (`gardusig/cli`):

```bash
docker build --target lint -f Dockerfile .
docker build --target repo-hygiene -f Dockerfile .
docker build --target unit-test -f Dockerfile .
```

## App-repo workflow surface

`cli structure check` in Docker `repo-hygiene` targets allows exactly one app-repo workflow file:

- `.github/workflows/pull-request.yml`

Each repo also owns one pipeline config file:

- `.github/pull-request.yaml`

Hub orchestration (extra workflows, shared `cli-base` / `operator` images) stays in `github-pipelines`.

`repo-hygiene` jobs declare `hygiene_policy` in `.github/pull-request.yaml`. The reusable workflow forwards that policy to Docker as `HYGIENE_POLICY_JSON`, and the Docker target runs `cli structure check --policy-file` to enforce allowed languages and metadata files.

## Layout by repo type

- `python-cli`: `src/`, `docs/`, `tests/`, `config/`, `Dockerfile`, `.github/pull-request.yaml`
- Language libraries: `src/`, `docs/`, `tests/`, `Dockerfile`
- `github-pipelines`: `.github/`, `docker/` (hub images only), `docs/`, `Dockerfile`

## Resolve flow

```mermaid
flowchart LR
  caller["App .github/workflows/pull-request.yml"] --> hub["pipelines pull-request.yml"]
  hub --> appConfig[".github/pull-request.yaml"]
  appConfig --> dockerfile["App Dockerfile"]
  dockerfile --> runDockerJob["cli pipeline docker run"]
```
