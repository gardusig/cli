# Quick defaults

Pass **`--yes`** / **`-y`** to skip interactive write gates.

| Command | Default behavior | Example |
| --- | --- | --- |
| `cli git commit` | Message `.` | `cli git commit -m .` |
| `cli git push` | Add, commit `.`, push current branch | `cli git push --yes` |
| `cli git reset` | Sync main, optional branch cleanup | `cli git reset --yes --delete-merged` |
| `cli git start` | Align main, create branch | `cli git start wip-250713-01 --yes` |
| `cli git deploy` | Tag when main ahead of latest tag | `cli git deploy --yes` |
| `cli ship` | Stage all, commit `.`, push main | `cli ship` |

See [workflows.md](workflows.md) for the full lifecycle.
