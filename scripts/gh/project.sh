#!/usr/bin/env bash
set -euo pipefail
if command -v cli >/dev/null 2>&1; then
  exec cli gh project "$@"
fi
echo "GitHub Projects blocked from CLI — use issues, labels, and backlog tree instead." >&2
echo "See docs/gh.md#blocked-commands" >&2
exit 1
