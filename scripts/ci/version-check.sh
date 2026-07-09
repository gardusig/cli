#!/usr/bin/env bash
# Compare PR/worktree version (copied pyproject.toml) against BASE_VERSION from the host.
# Docker builds must pass --build-arg BASE_VERSION=…; .git is never available in the image.
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(ci_repo_root)"
cd "$root"

if [[ -z "${BASE_VERSION:-}" ]]; then
  echo "BASE_VERSION is required (resolve on the host, e.g. scripts/ci/host-base-version.sh)" >&2
  exit 1
fi

head_version="$(ci_read_project_version "$root")"
ci_compare_versions "$BASE_VERSION" "$head_version"
