#!/usr/bin/env bash
# Shared Docker harness: build image, copy host tree into an isolated workdir, run commands.
set -euo pipefail

DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$DOCKER_DIR/../.." && pwd)}"
DOCKERFILE="${CLI_DOCKERFILE:-$ROOT/Dockerfile}"
DOCKER_TARGET="${CLI_DOCKER_TARGET:-integration}"
CONTAINER_SRC="/workspace/src"
CONTAINER_WORK="/tmp/cli"

docker_default_image_for_target() {
  case "$1" in
    python) echo "cli:python" ;;
    unit) echo "cli:unit" ;;
    integration) echo "cli:integration" ;;
    contest) echo "cli-contest:runner" ;;
    *) echo "cli:integration" ;;
  esac
}

IMAGE="${CLI_DOCKER_IMAGE:-$(docker_default_image_for_target "$DOCKER_TARGET")}"

docker_require() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH" >&2
    exit 127
  fi
}

docker_ensure_image() {
  docker_require
  if [[ "${CLI_DOCKER_SKIP_BUILD:-0}" != "1" ]]; then
    echo "Building image: $IMAGE (target=$DOCKER_TARGET)"
    docker build -f "$DOCKERFILE" --target "$DOCKER_TARGET" -t "$IMAGE" "$ROOT"
    if [[ "$DOCKER_TARGET" == "integration" && "$IMAGE" != "cli:dev" ]]; then
      docker tag "$IMAGE" cli:dev
    fi
    return 0
  fi
  echo "Using pre-built image: $IMAGE"
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    if [[ "$IMAGE" == "cli:integration" ]] && docker image inspect cli:dev >/dev/null 2>&1; then
      return 0
    fi
    echo "ERROR: CLI_DOCKER_SKIP_BUILD=1 but image not found: $IMAGE" >&2
    exit 1
  fi
}

# shellcheck disable=SC2120
docker_copy_workspace_script() {
  local dest="${1:-$CONTAINER_WORK}"
  cat <<EOF
set -euo pipefail
mkdir -p '$dest'
tar \\
  --exclude='.git' \\
  --exclude='.venv' \\
  --exclude='__pycache__' \\
  --exclude='.pytest_cache' \\
  --exclude='.integration-scratch' \\
  -C '$CONTAINER_SRC' \\
  -cf - . | tar -C '$dest' -xf -
EOF
}

docker_git_global_config() {
  cat <<'EOF'
git config --global user.email 'cli@example.test'
git config --global user.name 'Cli Test'
git config --global --add safe.directory '*'
EOF
}

docker_init_git_workspace() {
  local workdir="${1:-$CONTAINER_WORK}"
  local message="${2:-docker test snapshot}"
  cat <<EOF
$(docker_git_global_config)
env -u GIT_DIR -u GIT_WORK_TREE git -C '$workdir' init -b main
env -u GIT_DIR -u GIT_WORK_TREE git -C '$workdir' add -A
env -u GIT_DIR -u GIT_WORK_TREE git -C '$workdir' commit -m '$message'
EOF
}

docker_setup_git_workspace() {
  docker_init_git_workspace "${1:-$CONTAINER_WORK}" "docker integration snapshot"
}

# Run a bash script body inside a fresh container workdir (host repo mounted read-only).
# Optional second arg mounts /var/run/docker.sock for live integration checks.
docker_run_in_workspace() {
  local inner_script="$1"
  local mount_docker_sock="${2:-0}"
  docker_ensure_image
  local -a run_args=(
    --rm
    -v "$ROOT:$CONTAINER_SRC:ro"
    -e CLI_DOCKER_INTEGRATION=1
  )
  if [[ "$mount_docker_sock" == "1" ]]; then
    if [[ ! -S /var/run/docker.sock ]]; then
      echo "ERROR: /var/run/docker.sock not found (install Docker Desktop or the Docker engine)" >&2
      exit 1
    fi
    run_args+=(-v /var/run/docker.sock:/var/run/docker.sock)
    mkdir -p "$ROOT/.integration-scratch"
    run_args+=(
      -v "$ROOT/.integration-scratch:/integration-scratch:rw"
      -e CLI_CONTEST_WORKSPACE_ROOT=/integration-scratch
      -e CLI_CONTEST_WORKSPACE_HOST_ROOT="$ROOT/.integration-scratch"
    )
  fi
  docker run "${run_args[@]}" "$IMAGE" bash -c "$inner_script"
}
