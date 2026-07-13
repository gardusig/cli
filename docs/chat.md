# Chat (`cli opencode chat`)

Planning chat stores transcripts and artifacts under the configured chat directory.

## Flow

1. `cli opencode chat new SESSION`
2. Append messages during planning
3. `cli opencode chat distill SESSION` — R1 extraction JSON
4. `cli opencode chat categorize SESSION` — structured plan JSON (local only)

Applying categorize output does **not** create remote issues; review artifacts locally.

## Related

- [opencode.md](opencode.md)
