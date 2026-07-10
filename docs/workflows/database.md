# database

`gardusig/database` owns vault data and task pairs. It does not own workflows or Dockerfiles.

## Pull request

- `markdown`: lint `.md` / `.mdx` files and validate fenced Mermaid diagrams
- `validate`: catalog and document lifecycle rules
- `repo-hygiene`: reject `.github/workflows`, `Dockerfile`, and `docker/`
- `validate-tasks`: validate `tasks/tasks.pairs.json` against `tasks/header` and `tasks/body`

## CLI workflows

Separate workflow definitions should live under `.github/workflows/cli/private/`. They run from `gardusig/cli`, check out `gardusig/database` for task data, and install `gardusig/python-cli` for the CLI commands.

| Workflow | Command sequence | Write behavior |
| --- | --- | --- |
| `private-notion-cleanup` | `cli notion cleanup --yes` | Archives every page in the configured Notion database |
| `private-notion-deploy` | `cli tasks pairs build` -> `cli validate tasks` -> `cli notion deploy --yes` | Publishes enabled task pairs to Notion |
| `private-notion-ingest-pr` | `cli tasks ingest-pr --source notion --yes` | Opens a PR with Notion-sourced task changes |
| `private-notion-sync` | `cli notion ingest` -> `cli notion deploy --yes` | Reconciles Notion and local task pairs |
| `private-tasks-pairs-build` | `cli tasks pairs build` | Rebuilds `tasks.pairs.json` |
| `private-tasks-pairs-validate` | `cli validate tasks` | Read-only validation gate |
| `private-gh-issues-delete` | delete all issues from `gardusig/database` | Destructive preflight for a full task board reset |
| `private-gh-issues-insert` | insert every enabled task pair as a GitHub Issue | Recreates the issue set from local task data |
| `private-gh-issues-board-order` | reconcile Project membership -> update board order | Makes the board/project match task source order |
| `private-gh-issues-deploy` | `private-gh-issues-delete` -> `private-gh-issues-insert` -> `private-gh-issues-board-order` | Full reset/recreate/order workflow |
| `private-gh-issues-project` | add or reconcile deployed issues in the configured GitHub Project | Named Project integration only |
| `private-gh-issues-ingest-pr` | `cli tasks ingest-pr --source github --yes` | Opens a PR with GitHub-sourced task changes |
| `private-gh-issues-prune-closed` | `cli gh issues prune --closed-older-than 7d --yes` | Deletes filtered closed issues; does not close issues |

The GitHub Issues deploy workflow is intentionally ordered:

1. Delete all existing issues from the target repo.
2. Insert all enabled task issues from `gardusig/database/tasks`.
3. Reconcile Project membership and update board order.

Direct ad hoc `cli gh project ...` remains blocked. Project changes are allowed only inside named reviewed workflows such as `private-gh-issues-board-order` or `private-gh-issues-deploy`.

## Existing tasks router

Manual `tasks.yml` actions remain as the current router-backed entry points:

- `notion-deploy`
- `github-deploy`
- `notion-ingest-pr`
- `github-ingest-pr`
- `github-prune-closed`

These actions should converge with the separate CLI workflow catalog. Secrets are configured in `gardusig/cli`; see `docs/secrets.md`.

## Repo review

Manual `repo-review.yml` jobs:

- `repo-hygiene`
- `validate-tasks`

These give the database repo an explicit review workflow without deploying to remote APIs.
