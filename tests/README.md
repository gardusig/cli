# Tests

| Directory | Focus |
| --- | --- |
| `cli/` | Root CLI, links, configure, test packages |
| `git/` | Git shortcuts and deploy |
| `notion/` | Task pairs and sync |
| `drive/` | Tag zip backup |
| `chrome/` | Bookmarks |
| `docker/` | Container helpers |
| `contest/` | Validate harness |
| `integration/` | Registry gates and package resolution |
| `meta/` | Coverage, structure, external clients |
| `pack/` | Release smoke epics |
| `harness/` | Shared mocks (`drive_harness`, `notion_harness`, …) |

## Selective packages

```bash
cli test packages resolve --changed-path src/commands/git.py --format json
cli test packages run git --dry-run --format table
```

## Integration (Docker)

```bash
python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
```
