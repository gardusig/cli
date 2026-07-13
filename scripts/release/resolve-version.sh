#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_resolve_release_version() {
  local root version
  root="$(gh_repo_root)"
  cd "$root"
  version="$(gh_read_project_version "$root")"
  gh_write_output version "$version"
}

stage_run_with_timeout "${CI_RESOLVE_TIMEOUT}" _resolve_release_version
