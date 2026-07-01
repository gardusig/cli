# Pack scripts

Install tooling for **cursor-skills** (not workspace-ephemeral `.cursor/gh/` drafts).

| Script | Purpose |
| --- | --- |
| [`install.sh`](install.sh) | Copy `skills/**` into `~/.cursor/skills` (flat names); `--clean`, `--verify-only`, `--dry-run` |
| [`run.sh`](run.sh) | Run all pack checks under [`.cursor/tests/`](../tests/) |

From repo root:

```bash
./.cursor/scripts/install.sh
./.cursor/scripts/run.sh    # same as ./.cursor/tests/run.sh
```

Checks inventory: [`.cursor/tests/README.md`](../tests/README.md).
