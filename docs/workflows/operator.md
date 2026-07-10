# Operator workflows

Headless operator lanes built on `ghcr.io/gardusig/operator-runner` and `gardusig-cli`
selective test contracts.

## Operator test

**File:** `.github/workflows/operator-test.yml`

Resolves changed paths to CLI test packages; runs focused `cli test packages run`
legs in the operator-runner container. Falls back to the full `pull-request.yml`
router when selective resolve requests a full suite.

### Triggers

- `workflow_dispatch` — manual operator test
- `workflow_call` — reusable from `operator-dispatch.yml`

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `repository` | (required) | e.g. `gardusig/python-cli` |
| `ref` | (required) | Branch ref |
| `sha` | — | Commit SHA (preferred checkout) |
| `base` | `main` | Base ref for `git diff` resolve |
| `package_limit` | `4` | Selective package cap |
| `pipeline` | — | Passed to full-suite `pull-request` router |

### Example

```bash
gh workflow run operator-test.yml -R gardusig/cli \
  -f repository=gardusig/python-cli \
  -f ref=feat/language-first-cli-and-structure \
  -f sha="$(git rev-parse HEAD)"
```

### Contract

Uses `cli test packages resolve --base origin/main --head HEAD` from
`gardusig/python-cli`. See `docs/hub-operator.md` in the CLI repo.

## Operator craft plan

**File:** `.github/workflows/operator-craft-plan.yml`

Gathers issue context and prints an implementation plan via `cli opencode gh issue
--plan-only`. Uploads the plan as a workflow artifact; optional issue comment when
`comment=true` and `comment_yes=true`.

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `repository` | (required) | e.g. `gardusig/python-cli` |
| `issue` | (required) | Issue number |
| `ref` | (required) | Branch ref for checkout |
| `sha` | — | Commit SHA (preferred checkout) |
| `comment` | `false` | Post plan on issue |
| `comment_yes` | `false` | Confirm GitHub write for comment |

### Example

```bash
gh workflow run operator-craft-plan.yml -R gardusig/cli \
  -f repository=gardusig/python-cli \
  -f issue=81 \
  -f ref=main
```

## Operator craft execute

**File:** `.github/workflows/operator-craft-execute.yml`

Runs `cli opencode gh execute` checkpoints. Requires `yes=true` and
`DEEPSEEK_API_KEY`. Optional `handoff_pr=true` for craft PR handoff (needs
`contents: write`).

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `repository` | (required) | e.g. `gardusig/python-cli` |
| `issue` | (required) | Issue number |
| `ref` | (required) | Branch ref for checkout |
| `sha` | — | Commit SHA (preferred checkout) |
| `yes` | (required) | Must be `true` to run |
| `handoff_pr` | `false` | Hand off to `cli opencode gh pr` |
| `comment` | `true` | Post execute report on issue |

## Operator review

**File:** `.github/workflows/operator-review.yml`

AI PR review via `cli opencode gh review` (no merge). Uploads JSON summary artifact;
posts PR comment when `comment=true` and `comment_yes=true` (defaults).

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `repository` | (required) | e.g. `gardusig/python-cli` |
| `pr` | (required) | Pull request number |
| `issue` | — | Primary linked issue |
| `ref` | (required) | Branch ref for checkout |
| `sha` | — | Commit SHA (preferred checkout) |
| `comment` | `true` | Post review on PR |
| `comment_yes` | `true` | Confirm GitHub write for comment |

### Example

```bash
gh workflow run operator-review.yml -R gardusig/cli \
  -f repository=gardusig/python-cli \
  -f pr=88 \
  -f issue=81 \
  -f ref=feat/language-first-cli-and-structure \
  -f sha="$(git rev-parse HEAD)"
```

## Operator dispatch

**File:** `.github/workflows/operator-dispatch.yml`

Routes `lane` to the matching operator reusable workflow. Triggered by
`workflow_dispatch`, `repository_dispatch` (`event_type: operator`), or
`cli deploy operator LANE … --yes`.

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `lane` | (required) | `test` \| `plan` \| `execute` \| `review` |
| `repository` | (required) | e.g. `gardusig/python-cli` |
| `ref` | (required) | Branch ref |
| `sha` | — | Commit SHA (preferred checkout) |
| `issue` | — | Issue number (`plan` / `execute`) |
| `pr` | — | PR number (`review`) |
| `yes` | `false` | Required `true` for `execute` lane |

### Example

```bash
gh workflow run operator-dispatch.yml -R gardusig/cli \
  -f lane=test \
  -f repository=gardusig/python-cli \
  -f ref=main \
  -f sha="$(git rev-parse origin/main)"
```

## Related

- `docker/operator.dockerfile` — runner image
- `.github/workflows/operator-runner-publish.yml` — ghcr publish
- `.github/workflows/pull-request.yml` — full Docker PR pipeline
