#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace

if [[ -z "${CLI_LINT_LANGUAGES:-}" ]]; then
  echo "ERROR: CLI_LINT_LANGUAGES is empty" >&2
  exit 1
fi

cli_cmd=$(resolve_cli)
for language in $CLI_LINT_LANGUAGES; do
  echo "==> lint $language"
  # shellcheck disable=SC2086
  $cli_cmd lint "$language" "$WORKSPACE"
done

echo "repo lint ok"

