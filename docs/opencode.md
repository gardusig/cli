# OpenCode — AI entry point

All AI interactions go through **`cli opencode`**. Deterministic GitHub/git operations stay on **`cli gh`** and **`cli git`**.

## Domains

| Domain | Command | Purpose |
|--------|---------|---------|
| Raw prompts | `cli opencode plan\|summarize\|code\|categorize` | Direct DeepSeek tiers |
| Chat | `cli opencode chat …` | Multi-repo planning sessions |
| GitHub | `cli opencode gh …` | Issues, PRs, review (AI-assisted) |

## Models

| Role | Default model | CLI tier |
|------|---------------|----------|
| `reason` | `deepseek-reasoner` | `opencode plan`, `opencode code` |
| `chat` | `deepseek-chat` | `opencode summarize` |
| `categorize` | `deepseek-chat` | `opencode categorize`, chat categorize |

Configure in [`config/deepseek/models.yaml`](../config/deepseek/models.yaml). Set `DEEPSEEK_API_KEY`.

## GitHub domain (`cli opencode gh`)

| Command | Purpose |
|---------|---------|
| `gh issue` | Plan, review, ship issues |
| `gh pick` | List / pick issues |
| `gh next` | Backlog next + context |
| `gh execute` | Checkpoint execution |
| `gh pr` | Implement issue → PR |
| `gh review N` | AI PR review (no merge) |
| `gh draft` | Local issue draft file |

Deterministic reads/writes without AI: **`cli gh issue list`**, **`cli gh pr create`**, etc. — see [gh.md](gh.md).

## Cost Boundary

Anything under `cli opencode ...` may call OpenCode or DeepSeek and can spend API tokens.
Do not hide those calls behind deterministic commands such as `cli gh` or `cli test`.

Implementation rule:

- Keep paid/API-backed command handlers auditable under the OpenCode command boundary.
- Compatibility aliases such as `cli craft`, `cli chat`, `cli review`, and `cli ai` should remain thin wrappers around the OpenCode domain.
- New issue workflows should gather context with `cli gh`, resolve tests with `cli test packages`, and only call `cli opencode gh ...` when the user explicitly wants AI planning or execution help.

Before adding more AI-backed command files, prefer moving the implementation into a
dedicated `src/commands/opencode/` package while preserving the public `cli opencode ...`
command names.

## Chat domain (`cli opencode chat`)

```bash
cli opencode chat start
cli opencode chat send "plan hub operator across repos"
cli opencode chat distill
cli opencode chat categorize
cli opencode chat issues --apply --yes
```

See [chat.md](chat.md).

## Ship lane

```bash
cli opencode gh next
cli git reset --yes --main-only
cli git start issue-42 --yes
cli opencode gh execute 42 --pr --yes
cli opencode gh review 86 --issue 42 --yes
# merge in GitHub UI with a closing keyword in the PR body
```

## Issue planning lane

```bash
cli gh --repo gardusig/python-cli backlog next --format json
cli gh --repo gardusig/python-cli issue context 81 --format json
cli opencode gh issue --number 81 --plan --plan-only
cli test packages resolve --changed-path src/services/test_packages.py --changed-path src/commands/test_cmd.py
```

The first two commands are deterministic GitHub reads. The OpenCode command is the explicit
token-spending step. The final resolver command tells the operator which focused tests to
run after code changes.

## Backward-compatible aliases (hidden)

`cli craft`, `cli chat`, `cli review`, `cli ai` still work but prefer `cli opencode …`.

## See also

- [hub-operator.md](hub-operator.md) — headless ship lane, CI runner, epic progress
- [workflows.md](workflows.md) — git/gh lifecycle
- [gh.md](gh.md) — deterministic GitHub commands
