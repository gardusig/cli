#!/usr/bin/env bash
set -euo pipefail
exec cli opencode gh review "$@"
