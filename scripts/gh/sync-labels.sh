#!/usr/bin/env bash
# Sync config/gh/labels.manifest.yaml to GitHub (requires gh auth).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli gh label sync --manifest "$ROOT/config/gh/labels.manifest.yaml" --yes
