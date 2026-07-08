# Hub operator

Headless operator lane for [`gardusig/cli`](https://github.com/gardusig/cli): deterministic **`cli gh`** / **`cli git`** /
**`cli test`**, optional token spend on **`cli opencode`**, and CI images/workflows owned by
**`gardusig/yaml`**.

Parent tracking: **`epic:hub-operator`** (`config/gh/phase5/cli.batch.yaml`).

## Boundaries

| Layer | Owns |
| --- | --- |
| `gardusig/cli` | Application code, in-repo PR/release `Dockerfile`, `scripts/ci/`, command contracts |
| `gardusig/yaml` | Hub workflow routers, operator images, schedules, shared secrets |

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
| `cli gh issue context N` | Issue + epic + comment context (JSON); use `--transport api` in CI |
| `cli git reset/start/push` | Branch lifecycle ([workflows.md](workflows.md)) |
| `cli test packages resolve` | Changed paths → package matrix for CI |
| `cli test packages run PKG` | Focused unit/integration leg |
| `cli opencode gh issue --plan-only` | Implementation plan (no GitHub write) |
| `cli opencode gh execute` | AI implementation → PR (explicit `--yes`) |
| `cli opencode gh review` | AI PR review (no merge) |
| `cli pipeline run pull-request …` | Dispatch hub CI for an app repo |
| `cli deploy pull-request …` | Same as `pipeline run pull-request` (operator alias) |
| `cli deploy operator LANE …` | Dispatch `operator-dispatch.yml` (`test`/`plan`/`execute`/`review`) |
| `cli deploy release …` | Dispatch hub release workflow |
| `cli release main --yes` | PyPI + tag locally (maintainer, `PYPI_API_TOKEN`) |

**Blocked by policy:** `cli gh pr merge`, `cli gh issue close`, `cli gh ruleset` — merge in
GitHub UI. See [gh.md](gh.md#blocked-commands).

## Ship lane (local)

```bash
cli gh --repo gardusig/cli backlog next --format json
cli gh --transport api --repo gardusig/cli issue context 81 --format json
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
  --repository gardusig/cli \
  --ref feat/epic-06d-release \
  --sha "$(git rev-parse HEAD)"
```

Canonical GitHub repo: **`gardusig/cli`**. `cli pipeline config resolve` maps `gardusig/cli` →
`gardusig/cli` for hub YAML keys (`src/services/pipeline_runtime.py`). Legacy slug
`gardusig/cli` still dispatches successfully.

Hub workflow: `gardusig/yaml` → **Pull request** (`repository_dispatch`).

Equivalent deploy aliases:

```bash
cli deploy pull-request python-cli \
  --repository gardusig/cli \
  --ref feat/epic-06d-release \
  --sha "$(git rev-parse HEAD)" --yes

cli deploy operator test \
  --repository gardusig/cli \
  --ref feat/epic-06d-release \
  --sha "$(git rev-parse HEAD)" --yes

cli deploy operator plan \
  --repository gardusig/cli \
  --issue 81 \
  --ref main --yes
```

### Selective resolve JSON contract

`cli test packages resolve --format json` returns:

| Field | Type | Meaning |
| --- | --- | --- |
| `changed_paths` | `string[]` | Normalized repo-relative paths |
| `package_names` | `string[]` | Packages to run in selective CI |
| `packages` | `object[]` | Full package records + match reasons |
| `full_suite` | `bool` | When true, run full PR pipeline |
| `full_suite_reasons` | `string[]` | Why selective CI was skipped |
| `requires_ai` / `costs_api_tokens` | `bool` | Matched packages need OpenCode |
| `pipeline_contract` | `object` | Hub job names for package legs |

### Runner image (Phase B)

Slim image for workflow jobs that only need `cli`, `git`, `gh`, and optional Docker socket:

- Dockerfile: `gardusig/yaml/docker/operator.dockerfile`
- Target: `operator-runner`
- Publish: `ghcr.io/gardusig/operator-runner` (workflow `operator-runner-publish.yml`)

Pin `CLI_VERSION` at build time after PyPI releases; local dev may use editable install.

### Reusable workflows

`workflow_call` entrypoints in `gardusig/yaml`:

| Workflow | Status |
|----------|--------|
| `operator-test.yml` | **Shipped** — selective resolve + package matrix; full-suite → pull-request router |
| `operator-craft-plan.yml` | **Shipped** — issue context + `cli opencode gh issue --plan-only` |
| `operator-craft-execute.yml` | **Shipped** — `cli opencode gh execute` (`yes` gate + `DEEPSEEK_API_KEY`) |
| `operator-review.yml` | **Shipped** — `cli opencode gh review` (no merge) |
| `operator-dispatch.yml` | **Shipped** — routes `lane` → test/plan/execute/review reusables |

Docs: `gardusig/yaml/docs/workflows/operator.md`.

Dispatch examples:

```bash
gh workflow run operator-dispatch.yml -R gardusig/gardusig/yaml \
  -f lane=test \
  -f repository=gardusig/cli \
  -f ref=feat/language-first-cli-and-structure \
  -f sha="$(git rev-parse HEAD)"

gh workflow run operator-test.yml -R gardusig/gardusig/yaml \
  -f repository=gardusig/cli \
  -f ref=feat/language-first-cli-and-structure \
  -f sha="$(git rev-parse HEAD)"

gh workflow run operator-craft-plan.yml -R gardusig/gardusig/yaml \
  -f repository=gardusig/cli \
  -f issue=81 \
  -f ref=main

gh workflow run operator-review.yml -R gardusig/gardusig/yaml \
  -f repository=gardusig/cli \
  -f pr=88 \
  -f issue=81 \
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

## See also

- [ci-workflows.md](ci-workflows.md) — PR and release Docker pipeline
- [release.md](release.md) — PyPI lane
- [public-cli-hardening.md](public-cli-hardening.md) — public CLI hardening checklist
