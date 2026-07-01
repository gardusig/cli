#!/usr/bin/env bash
set -euo pipefail
echo "merge blocked: use GitHub UI or enable auto-merge on the PR." >&2
echo "CLI does not merge PRs (policy). See docs/workflows.md#merge-policy" >&2
exit 1
