#!/usr/bin/env bash
# Build cli-contest:runner (contest stage from Dockerfile).
set -euo pipefail
export CLI_DOCKER_TARGET=contest
export CLI_DOCKER_IMAGE="${CLI_CONTEST_IMAGE:-cli-contest:runner}"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
docker_require
echo "Building $IMAGE from $ROOT (Dockerfile --target contest)"
docker build -f "$DOCKERFILE" --target contest -t "$IMAGE" "$ROOT"
echo "Built: $IMAGE"
