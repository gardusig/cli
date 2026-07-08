#!/usr/bin/env bash
# Post-install integration for pip-published gardusig-cli (artifact under test).
set -euo pipefail
# shellcheck source=scripts/ci/consumer/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

live_docker=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --live-docker)
      live_docker=1
      shift
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v cli >/dev/null 2>&1; then
  echo "cli binary not found on PATH after pip install" >&2
  exit 1
fi

export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$(consumer_root)/../../config/ci}"
if [[ ! -d "$CLI_CONFIG_DIR" ]]; then
  export CLI_CONFIG_DIR="$(consumer_root)/fixtures/config"
fi

cli --help >/dev/null
cli --version >/dev/null
cli languages list >/dev/null
cli lint --help >/dev/null
cli git --help >/dev/null
cli pypi --help >/dev/null

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
git -C "$tmpdir" init -q
git -C "$tmpdir" config user.email "consumer@test"
git -C "$tmpdir" config user.name "Consumer"
touch "$tmpdir/README.md"
git -C "$tmpdir" add README.md
git -C "$tmpdir" commit -q -m "init"
cli git --help >/dev/null

if (( live_docker )); then
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker not available for --live-docker" >&2
    exit 1
  fi
  cli docker --help >/dev/null
  cli docker stats --help >/dev/null
fi

echo "consumer integration passed (PYPI_INDEX=${PYPI_INDEX:-testpypi})"
