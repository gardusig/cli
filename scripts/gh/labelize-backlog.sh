#!/usr/bin/env bash
# Apply config/gh/backlog-labelize.batch.yaml (titles + labels on open issues).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli gh issue batch --file "$ROOT/config/gh/backlog-labelize.batch.yaml" --yes
