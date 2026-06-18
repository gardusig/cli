# GitHub Actions

## test.yml

Runs on **every push** (all branches) and on **pull requests** targeting any branch.

| Status check name | Job | Gate |
| --- | --- | --- |
| `Unit tests (Docker)` | `unit` | `./scripts/test-unit.sh` (≥80% coverage) |
| `Integration tests (Docker)` | `integration` | `./scripts/test-integration.sh` |

Pushes to a PR branch report the same checks on the pull request. `main` pushes get checks on the branch tip for post-merge verification.

## branch-protection.yml

Manual workflow to configure **branch protection** requiring both test checks.

1. Ensure at least one successful `test` run on `main` so check names exist in GitHub.
2. **Settings → Actions → General → Workflow permissions** → allow read/write (needed for branch protection API).
3. **Actions → branch-protection → Run workflow** (default branch: `main`).
4. Confirm under **Settings → Branches → Branch protection rules**.

To apply the same pattern on other repositories, copy `test.yml` (keep job `name:` fields identical) and run `branch-protection` once per repo.

## Manual setup (without workflow)

**Settings → Branches → Add rule** for `main`:

- Require status checks: `Unit tests (Docker)`, `Integration tests (Docker)`
- Require branches to be up to date before merging (matches `strict: true`)
