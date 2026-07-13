#!/usr/bin/env bash
# Compare PR version against the last published PyPI version (BASE_VERSION from host).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"

if [[ -z "${BASE_VERSION:-}" ]]; then
  echo "no published PyPI version yet — version gate skipped"
  exit 0
fi

head_version="$(gh_read_project_version "$root")"
stage_compare_versions "$BASE_VERSION" "$head_version"
