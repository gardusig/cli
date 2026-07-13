#!/usr/bin/env bash
# Post-install integration for pip-published gardusig-cli (artifact under test).
set -euo pipefail
# shellcheck source=scripts/pull-request/consumer/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
# shellcheck source=scripts/pull-request/_smoke.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_smoke.sh"

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

smoke_run_all

if (( live_docker )); then
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker not available for --live-docker" >&2
    exit 1
  fi
  cli docker --help >/dev/null
  cli docker stats --help >/dev/null
fi

echo "consumer integration passed (PYPI_INDEX=${PYPI_INDEX:-testpypi})"
