# Workflows

Git-first daily loop for local development. Use **`cli git`** for branch hygiene, commits, and tags.

## Lifecycle

```text
reset → start → work → push → review → [merge in hosting UI] → reset
```

| Step | Command |
| --- | --- |
| Return to synced main | `cli git reset --yes --delete-merged` |
| Start issue branch | `cli git start issue-slug --yes` |
| Commit and push | `cli git push --yes` |
| Local review gate | `cli git review` |
| Tag release on main | `cli git deploy --yes` |

## Personal backup

```bash
cli ship          # stage, commit ('.'), push main
```

## Related

- [git.md](git.md) — full command reference
- [quick-defaults.md](quick-defaults.md) — default flags
- [release.md](release.md) — PyPI release flow
