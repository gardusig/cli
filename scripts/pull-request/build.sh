#!/usr/bin/env bash
# docker build --target for pull-request Dockerfile
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

target="${1:?target required}"
shift

DOCKERFILE="${PR_DOCKERFILE}"
root="$(gh_repo_root)"
cd "$root"

stage_run_with_timeout "${CI_DOCKER_BUILD_TIMEOUT}" gh_docker_build "$target" "$@"
