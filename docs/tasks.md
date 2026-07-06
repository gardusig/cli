# Task Shortcuts

Task data lives in `gardusig/database/tasks`. The CLI provides reusable shortcuts only; workflow policy lives in `gardusig/github-pipelines`.

## Pair validation

```bash
cli validate tasks
cli tasks pairs build
```

## Ingest to PR

```bash
cli tasks ingest-pr --source notion --yes
cli tasks ingest-pr --source github --yes
```

The command only stages `tasks/`, commits to a sync branch, pushes, and opens a PR.

## Pipeline dispatch

```bash
cli pipeline run tasks database --action github-deploy
cli pipeline run repo-review python-cli --job version-check
```

The dispatch target is always `gardusig/github-pipelines`; app repos do not contain workflows.

## Named CLI workflows

The merged workflow catalog treats task operations as named workflows, not arbitrary `cli` argv passed through CI.

| Workflow | Sequence |
| --- | --- |
| `private-notion-deploy` | `cli tasks pairs build` -> `cli validate tasks` -> `cli notion deploy --yes` |
| `private-notion-ingest-pr` | `cli tasks ingest-pr --source notion --yes` |
| `private-gh-issues-deploy` | delete all repo issues -> insert all task issues -> update board/project order |
| `private-gh-issues-ingest-pr` | `cli tasks ingest-pr --source github --yes` |
| `private-gh-issues-prune-closed` | `cli gh issues prune --closed-older-than 7d --yes` |

GitHub Project updates are part of the named task-board workflows only. Direct ad hoc `cli gh project ...` remains blocked.
