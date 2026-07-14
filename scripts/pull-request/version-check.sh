#!/usr/bin/env bash
# Compare PR version against the greatest published PyPI/TestPyPI version (BASE_VERSION from host).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_run_version_check() {
  local root
  root="$(gh_repo_root)"
  cd "$root"

  if [[ -z "${BASE_VERSION:-}" ]]; then
    echo "no published PyPI/TestPyPI version yet — version gate skipped"
    return 0
  fi

  local head_version
  head_version="$(gh_read_project_version "$root")"
  stage_compare_versions "$BASE_VERSION" "$head_version"
}

stage_run_with_timeout "${CI_VERSION_CHECK_TIMEOUT}" _run_version_check
