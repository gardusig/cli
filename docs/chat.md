# Planning chat (`cli opencode chat`)

Also available as hidden alias `cli chat`.

Repo-agnostic conversation for multi-repo planning. Sessions live under `~/.config/cli/chat/` (or `CLI_CHAT_DIR`) — **not** inside any git repository.

## Models (DeepSeek only)

| Role | Model | Use |
|------|-------|-----|
| `chat` | `deepseek-chat` | Ongoing conversation + rolling summary |
| `reason` | `deepseek-reasoner` | R1 — extensive idea traversal |
| `categorize` | `deepseek-chat` | Pick topics; one parent epic per repo |

Configure in [`config/deepseek/models.yaml`](../config/deepseek/models.yaml). Override with `DEEPSEEK_MODEL_CHAT`, `DEEPSEEK_MODEL_REASON`, `DEEPSEEK_MODEL_CATEGORIZE`.

Set `DEEPSEEK_API_KEY` locally and as a GitHub Actions secret for workflows.

## Local flow

```bash
export DEEPSEEK_API_KEY=...

cli opencode chat start                    # new session
cli opencode chat send "cli breaking change may break yugioh workflows"
cli opencode chat send "also vague idea about notion on laptop only"
cli opencode chat summary                  # rolling plan summary
cli opencode chat distill                  # R1 — extract all themes + cross-repo risks
cli opencode chat categorize               # JSON plan: parent per repo + actions
cli opencode chat issues                   # distill + categorize (dry-run)
cli opencode chat issues --apply --yes     # comment/create on GitHub
```

## GitHub workflow

**Actions → chat-to-issues → Run workflow**

Paste your chat summary. Optionally enable **apply_issues** to file comments/create parents.

Same as:

```bash
cli opencode chat issues --from-file summary.md --apply --yes
```

Reusable from other repos:

```yaml
jobs:
  plan:
    uses: gardusig/pipelines/.github/workflows/reusable-plan-chat-to-issues.yml@main
    secrets: inherit
    with:
      chat_summary: ${{ inputs.summary }}
      apply_issues: false
```

## Output shape

Each repo in [`config/chat/repos.yaml`](../config/chat/repos.yaml) may get:

- One **parent epic** (`issue-type:epic`, `epic:<slug>`, `priority:N`)
- **Comments** on existing issues (`## [cli] plan`)
- **New children** for vague but useful ideas

Cross-repo impacts (e.g. cli API break affecting consumers) appear in `cross_repo_notes` on parent bodies.

## Not in scope

- GitHub Projects (use `cli gh backlog organize` instead)
- `cli gh pr merge` (UI only)
- Notion in CI — laptop-only; container uses chat summary only
