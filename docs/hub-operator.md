# Hub operator

Headless operator lane for `gardusig/python-cli`: deterministic **`cli gh`** / **`cli git`** /
**`cli test`**, optional token spend on **`cli opencode`**, and CI images/workflows owned by
**`gardusig/github-pipelines`**.

Parent tracking: **`epic:hub-operator`** (`config/gh/phase5/cli.batch.yaml`).

## Boundaries

| Layer | Owns |
| --- | --- |
| `python-cli` | Command contracts, policy guards, OpenCode domain, test package resolve |
| `github-pipelines` | Workflow YAML, Dockerfiles, `ghcr.io` images, schedules, secrets |

This repo must not add `.github/workflows/` or root `Dockerfile` files for operator CI.

## Cost boundary

- **Free reads / writes:** `cli gh issue list`, `cli gh issue context`, `cli git …`,
  `cli test packages resolve`, `cli pipeline run …`
- **Token spend:** anything under `cli opencode …` (plan, execute, review, chat)

Gather context with `cli gh` first; call `cli opencode gh …` only when AI help is intended.
See [opencode.md](opencode.md).

## Operator commands

| Command | Role in operator lane |
| --- | --- |
| `cli gh backlog next` | Pick next ready subissue (`gh_topo`, `priority:N`) |
| `cli gh issue context N` | Issue + epic + comment context (JSON) |
| `cli git reset/start/push` | Branch lifecycle ([workflows.md](workflows.md)) |
| `cli test packages resolve` | Changed paths → package matrix for CI |
| `cli test packages run PKG` | Focused unit/integration leg |
| `cli opencode gh issue --plan-only` | Implementation plan (no GitHub write) |
| `cli opencode gh execute` | AI implementation → PR (explicit `--yes`) |
| `cli opencode gh review` | AI PR review (no merge) |
| `cli pipeline run pull-request …` | Dispatch hub CI for an app repo |
| `cli release main --yes` | PyPI + tag (maintainer, `PYPI_API_TOKEN`) |

**Blocked by policy:** `cli gh pr merge`, `cli gh issue close`, `cli gh ruleset` — merge in
GitHub UI. See [gh.md](gh.md#blocked-commands).

## Ship lane (local)

```bash
cli gh --repo gardusig/python-cli backlog next --format json
cli gh --repo gardusig/python-cli issue context 81 --format json
cli git reset --yes --main-only
cli git start issue-81-slug --yes
cli opencode gh issue --number 81 --plan --plan-only
cli test packages resolve \
  --changed-path src/services/test_packages.py \
  --format json
# after edits
cli test packages run gh
cli git push --yes
cli gh pr create --title "…" --body "Closes #81"
cli opencode gh review 88 --issue 81 --yes   # optional; costs tokens
# merge in GitHub UI (auto-merge allowed)
cli git reset --yes --delete-merged
```

## CI operator lane

Dispatch full PR pipeline (use **full** `git rev-parse HEAD` SHA):

```bash
cli pipeline run pull-request python-cli \
  --repository gardusig/python-cli \
  --ref feat/language-first-cli-and-structure \
  --sha "$(git rev-parse HEAD)"
```

Hub workflow: `gardusig/github-pipelines` → **Pull request** (`repository_dispatch`).

### Runner image (Phase B)

Slim image for workflow jobs that only need `cli`, `git`, `gh`, and optional Docker socket:

- Dockerfile: `github-pipelines/docker/operator.dockerfile`
- Target: `operator-runner`
- Publish: `ghcr.io/gardusig/operator-runner` (workflow `operator-runner-publish.yml`)

Pin `CLI_VERSION` at build time after PyPI releases; local dev may use editable install.

### Reusable workflows

`workflow_call` entrypoints in `github-pipelines`:

| Workflow | Status |
|----------|--------|
| `operator-test.yml` | **Shipped** — selective resolve + package matrix; full-suite → `pull-request.yml` |
| `operator-craft-plan.yml` | Planned |
| `operator-craft-execute.yml` | Planned |
| `operator-review.yml` | Planned |

Docs: `github-pipelines/docs/workflows/operator.md`.

Dispatch example:

```bash
gh workflow run operator-test.yml -R gardusig/github-pipelines \
  -f repository=gardusig/python-cli \
  -f ref=feat/language-first-cli-and-structure \
  -f sha="$(git rev-parse HEAD)"
```

## Secrets

| Secret | Used by |
| --- | --- |
| `GITHUB_TOKEN` / `CENTRAL_PIPELINE_PAT` | checkout, `gh`, dispatch |
| `DEEPSEEK_API_KEY` | `cli opencode` only |
| `PYPI_API_TOKEN` | `cli release main`, TestPyPI legs |
| `TESTPYPI_API_TOKEN` | PR TestPyPI publish |

Break-glass: `CLI_ALLOW_GH_MERGE=1` allows raw `gh pr merge` inside providers (emergency only).

## Epic progress

| Child | Status |
| --- | --- |
| 0 — docs / snapshot | **This doc** + [opencode.md](opencode.md) |
| 1 — tag policy + hub CI | Shipped (Epic 06, `github-pipelines` PR #2) |
| 2 — forbid `cli gh pr merge` | Shipped (`gh_policy.py`) |
| 3 — runner image + ghcr | **Done** ([github-pipelines #11](https://github.com/gardusig/github-pipelines/pull/11)) |
| 4 — reusable `workflow_call` | **In progress** (`operator-test.yml` shipped) |
| 5–8 — OpenCode + `gh_topo` | Shipped on PR #88 |
| 9 — `test` / `deploy` / `release` | `test` + `release` shipped; `deploy` stub |
| 10 — dispatch orchestrator | Planned |

## See also

- [ci-workflows.md](ci-workflows.md) — selective test contract
- [release.md](release.md) — PyPI lane
- [public-cli-hardening.md](public-cli-hardening.md) — Epic 07 matrix
