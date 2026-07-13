#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

ref="${GITHUB_REF_NAME:-}"
if [[ -z "$ref" ]]; then
  echo "GITHUB_REF_NAME is required" >&2
  exit 1
fi
if [[ "$ref" != v* ]]; then
  echo "expected tag ref v*, got: $ref" >&2
  exit 1
fi

version="${ref#v}"
root="$(gh_repo_root)"
project_version="$(gh_read_project_version "$root")"
if [[ "$version" != "$project_version" ]]; then
  echo "tag/version mismatch: tag=$version pyproject=$project_version" >&2
  exit 1
fi

gh_write_output tag "$ref"
gh_write_output version "$version"
