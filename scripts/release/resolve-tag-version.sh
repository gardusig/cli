#!/usr/bin/env bash
# Resolve release coordinates from a pushed git tag (X.Y.Z).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_resolve_tag_version() {
  local ref git_tag version root project_version
  ref="${GITHUB_REF_NAME:-}"
  if [[ -z "$ref" ]]; then
    echo "GITHUB_REF_NAME is required (push a release tag)" >&2
    exit 1
  fi
  if [[ ! "$ref" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.]+)?$ ]]; then
    echo "expected semver tag X.Y.Z (optional v prefix), got: $ref" >&2
    exit 1
  fi

  git_tag="$ref"
  version="$(gh_strip_v_prefix "$ref")"
  root="$(gh_repo_root)"
  project_version="$(gh_read_project_version "$root")"
  if [[ "$version" != "$project_version" ]]; then
    echo "tag ${git_tag} (${version}) must match pyproject (${project_version})" >&2
    exit 1
  fi

  gh_write_output tag "$git_tag"
  gh_write_output git_tag "$git_tag"
  gh_write_output version "$version"
  gh_write_output pypi_version "$version"
  gh_write_output docker_tag "$version"
}

stage_run_with_timeout "${CI_RESOLVE_TIMEOUT}" _resolve_tag_version
