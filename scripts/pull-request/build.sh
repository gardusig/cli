#!/usr/bin/env bash
# docker build --target for pull-request.dockerfile
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

target="${1:?target required}"
shift

root="$(gh_repo_root)"
cd "$root"

gh_docker_build "$PR_DOCKERFILE" "$target" "$@"
