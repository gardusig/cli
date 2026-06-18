#!/usr/bin/env bash
# Build shuttle-contest:runner (contest stage from Dockerfile).
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
export SHUTTLE_DOCKER_TARGET=contest
export SHUTTLE_DOCKER_IMAGE="${SHUTTLE_CONTEST_IMAGE:-shuttle-contest:runner}"
docker_require
echo "Building $IMAGE from $ROOT (Dockerfile --target contest)"
docker build -f "$DOCKERFILE" --target contest -t "$IMAGE" "$ROOT"
echo "Built: $IMAGE"
