#!/usr/bin/env bash
# Build a cli Docker image stage (see Dockerfile).
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
docker_require
echo "Building $IMAGE from $ROOT (Dockerfile --target $DOCKER_TARGET)"
docker build -f "$DOCKERFILE" --target "$DOCKER_TARGET" -t "$IMAGE" "$ROOT"
if [[ "$DOCKER_TARGET" == "integration" && "$IMAGE" != "cli:dev" ]]; then
  docker tag "$IMAGE" cli:dev
  echo "Tagged: cli:dev"
fi
echo "Built: $IMAGE"
