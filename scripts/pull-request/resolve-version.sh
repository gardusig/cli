#!/usr/bin/env bash
# Resolve PR head version and last published PyPI version.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_resolve_versions() {
  local root
  root="$(gh_repo_root)"
  cd "$root"

  local version base_version
  version="$(gh_read_project_version "$root")"
  base_version="$(bash scripts/pull-request/host-last-published-version.sh)"

  gh_write_output version "$version"
  gh_write_output base_version "$base_version"
}

stage_run_with_timeout "${CI_RESOLVE_TIMEOUT}" _resolve_versions
