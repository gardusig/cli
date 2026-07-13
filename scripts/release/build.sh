#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

target="${1:?target required}"
shift

root="$(gh_repo_root)"
cd "$root"

gh_docker_build "$RELEASE_DOCKERFILE" "$target" "$@"
