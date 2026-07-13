# OpenCode (`cli opencode`)

All AI interactions go through **`cli opencode`**. Deterministic git operations stay on **`cli git`**.

## Domains

| Domain | Command | Purpose |
| --- | --- | --- |
| Chat | `cli opencode chat …` | Planning sessions, distill, categorize (local artifacts) |
| Tiers | `cli opencode plan\|summarize\|code\|categorize` | One-shot DeepSeek prompts |

## Examples

```bash
cli opencode plan "reason about release checklist"
cli opencode chat new my-session
cli opencode chat distill my-session
```

## Related

- [chat.md](chat.md) — planning chat artifacts
- [workflows.md](workflows.md) — git lifecycle shortcuts
- [git.md](git.md) — deterministic git commands
