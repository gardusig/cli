# Craft commands — cursor-skills @gh-* replacement

Replaces [`gardusig/cursor-skills`](https://github.com/gardusig/cursor-skills) `@gh-issue*`, `@gh-pr*`, `@gh-pr-review` with headless CLI flows powered by **OpenCode + DeepSeek** (three model roles).

## Model roles

| Role | Default model | Used for |
|------|---------------|----------|
| `reason` | `deepseek-reasoner` | Plans, issue review, PR review, execute checkpoints, codegen guidance |
| `categorize` | `deepseek-chat` | Dedupe verdicts, issue ship specs, labels |
| `chat` | `deepseek-chat` | PR body polish, summaries |

Override via `DEEPSEEK_MODEL_CHAT`, `DEEPSEEK_MODEL_REASON`, `DEEPSEEK_MODEL_CATEGORIZE` or [`config/deepseek/models.yaml`](../config/deepseek/models.yaml).

Set `DEEPSEEK_API_KEY` for live output. Without it, commands return structured stubs (CI-safe).

Optional: install [`opencode`](https://github.com/opencode-ai/opencode) on PATH — `craft pr` uses it for `tier=code` when available.

## Skill → command map

| cursor-skills | cli |
|---------------|-----|
| `@gh-issue` | `cli craft issue --title … --body-file … --yes` |
| `@gh-issue-review` | `cli craft issue --review -n N` |
| `@gh-issue-pick` | `cli craft pick` / `cli craft pick -n N` |
| `@gh-issue-next` | `cli craft next` |
| `@gh-issue-execute` | `cli craft execute N` / `cli craft execute N --pr --yes` |
| `@gh-pr` | `cli craft pr -n N --yes` |
| `@gh-pr-review` | `cli review pr N` |
| `@gh-issue-backlog` | `cli gh backlog organize` |
| `@gh-issue-labels` | `cli gh label sync` |

Read-only gh commands (`issue list`, `pr view`, …) unchanged — see [gh.md](gh.md).

## Three-loop workflow

```bash
# 1. Ideas → issues
cli chat start
cli chat distill && cli chat categorize
cli chat apply --yes

# 2. Issue → PR
cli craft next
cli craft issue --plan -n 71 --yes
cli craft execute 71 --pr --yes

# 3. PR → merge (UI only)
cli review pr 86 --yes
# merge in GitHub UI — cli gh pr merge is blocked
```

## Examples

```bash
# Dedupe before ship
cli craft issue --title "2 — Hub workflows" --body-file body.md --dedupe-only

# Ship after Cursor Proceed
cli craft issue --title "2 — Hub workflows" --body-file body.md --yes

# Reshape report (read-only)
cli craft issue --review -n 42

# Plan comment on issue
cli craft issue --plan -n 42 --yes

# Pick + context
cli craft pick --label epic:hub
cli craft pick -n 42

# Execute checkpoints + open PR
cli craft execute 42 --pr --yes

# PR review with linked issue
cli review pr 86 --issue 42 --yes
```

## Write gates

Mutating craft commands require interactive confirm or `--yes` (after agent **Proceed**):

- `craft issue` (ship)
- `craft issue --plan`
- `craft execute` (comment)
- `craft execute --pr`
- `craft pr`
- `review pr --comment`

## Migration archive

Normative skill prose lives in [`docs/migration/cursor-skills/`](migration/cursor-skills/). Safe to delete the standalone `cursor-skills` repo once this doc and embedded snapshot are on `main`.

## See also

- [gh.md](gh.md) — deterministic `cli gh` commands
- [chat.md](chat.md) — multi-repo chat → issues
- `cli ai plan|summarize|code|categorize` — raw tier prompts
