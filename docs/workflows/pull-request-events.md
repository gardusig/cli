# Pull request events

## Model

1. **App repo** — `.github/workflows/pull-request.yml` triggers on `pull_request` to `main`.
2. **Caller** — `workflow_call` into `gardusig/cli/.github/workflows/pull-request.yml`.
3. **Router** — checks out the app repo and resolves `.github/pull-request.yaml` (falls back to central configs during migration).
4. **Stages** — each job runs one Docker target via `cli pipeline docker run`.

Checks appear on the PR in the **app repo** because the reusable workflow executes in the caller's Actions run.

## Workflow catalog

PR job graphs live in each app repo at `.github/pull-request.yaml`. Dockerfiles and reusable routers stay in `gardusig/cli`. See `docs/workflows/CATALOG.md` for repo coverage.

## Allowed app-repo workflow surface

`cli structure check` in Docker `repo-hygiene` targets allows exactly one app-repo workflow file:

- `.github/workflows/pull-request.yml`

Each repo also owns one pipeline config file:

- `.github/pull-request.yaml`

All other orchestration (Dockerfiles, extra workflows, `scripts/docker|test|deploy|release/`) must stay in `gardusig/cli` / `python-cli`.

`repo-hygiene` jobs declare `hygiene_policy` in `.github/pull-request.yaml`. The reusable workflow forwards that policy to Docker as `HYGIENE_POLICY_JSON`, and the Docker target runs `cli structure check --policy-file` to enforce allowed languages and metadata files.

## Manual / CLI fallback

`repository_dispatch` with `event_type: pull-request` still works for ad-hoc runs:

```bash
cli pipeline run pull-request python-cli --ref my-branch --sha "$(git rev-parse HEAD)"
cli pipeline run pull-request tex --ref my-branch
```
