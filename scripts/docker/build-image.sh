#!/usr/bin/env bash
# Build a shuttle-cli Docker image stage (see Dockerfile).
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
docker_require
echo "Building $IMAGE from $ROOT (Dockerfile --target $DOCKER_TARGET)"
docker build -f "$DOCKERFILE" --target "$DOCKER_TARGET" -t "$IMAGE" "$ROOT"
if [[ "$DOCKER_TARGET" == "integration" && "$IMAGE" != "shuttle-cli:dev" ]]; then
  docker tag "$IMAGE" shuttle-cli:dev
  echo "Tagged: shuttle-cli:dev"
fi
echo "Built: $IMAGE"
