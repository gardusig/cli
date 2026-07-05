#!/usr/bin/env bash
set -euo pipefail
if command -v cli >/dev/null 2>&1; then
  exec cli gh ruleset "$@"
fi
echo "GitHub Rulesets blocked from CLI — configure in the GitHub UI." >&2
echo "See docs/gh.md#blocked-commands" >&2
exit 1
