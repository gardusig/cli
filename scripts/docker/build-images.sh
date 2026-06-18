#!/usr/bin/env bash
# Build all Docker image stages (python, unit, integration, contest).
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
docker_require
for target in python unit integration contest; do
  image="$(docker_default_image_for_target "$target")"
  echo "==> $target -> $image"
  docker build -f "$DOCKERFILE" --target "$target" -t "$image" "$ROOT"
done
docker tag shuttle-cli:integration shuttle-cli:dev
echo "Tagged: shuttle-cli:dev -> shuttle-cli:integration"
echo "All stages built."
