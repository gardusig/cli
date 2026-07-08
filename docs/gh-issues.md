# GitHub Issues Sync

`cli gh issues` syncs `gardusig/database/tasks` with GitHub Issues on `gardusig/database`.

## Deploy

```bash
cli gh issues deploy --dry-run
cli gh issues deploy --yes
```

Deploy is the destructive full-board reset for task issues in the configured private repo:

1. Delete all existing issues from the target repo.
2. Insert all enabled task pairs as GitHub Issues.
3. Reconcile the configured GitHub Project and update board/order metadata.

The pipeline-backed workflow name is `private-gh-issues-deploy`. The lower-level catalog entries are `private-gh-issues-delete`, `private-gh-issues-insert`, and `private-gh-issues-board-order`.

## Ingest

```bash
cli gh issues ingest --yes
```

Ingest writes GitHub Issues into local task headers/bodies. Prefer `cli tasks ingest-pr --source github --yes` so changes are reviewed through a PR.

## Prune

```bash
cli gh issues prune --closed-older-than 7d --dry-run
cli gh issues prune --closed-older-than 7d --yes
```

Prune deletes filtered closed issues. It does not close issues. Direct issue close is blocked; merge PRs in the GitHub UI and let closing keywords auto-close issues.

## Policy

Blocked:

- `cli gh pr merge`
- `cli gh issue close`
- `cli gh issue batch` entries with `action: close`
- Ad hoc `cli gh project ...` and Rulesets through CLI

GitHub Project updates are allowed only through reviewed task-board workflows. Use top-level `cli project ...` for local command workflows; keep pipeline orchestration in `gardusig/yaml`.
