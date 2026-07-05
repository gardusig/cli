#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

command -v markdownlint-cli2 >/dev/null 2>&1 || {
  echo "ERROR: markdownlint-cli2 is required" >&2
  exit 1
}

mapfile -t markdown_files < <(find . \
  \( -path './.git' -o -path './node_modules' -o -path './.venv' \) -prune -o \
  -type f \( -name '*.md' -o -name '*.mdx' \) -print | sort)

if [[ ${#markdown_files[@]} -eq 0 ]]; then
  echo "markdown lint skipped: no markdown files"
  exit 0
fi

markdownlint-cli2 "${markdown_files[@]}"

if command -v mmdc >/dev/null 2>&1; then
  tmp_dir=$(mktemp -d)
  trap 'rm -rf "$tmp_dir"' EXIT
  index=0
  for file in "${markdown_files[@]}"; do
    awk -v out="$tmp_dir" -v base="$index" '
      /^```mermaid[[:space:]]*$/ { in_block=1; n++; next }
      /^```[[:space:]]*$/ && in_block { in_block=0; next }
      in_block { print > (out "/mermaid-" base "-" n ".mmd") }
    ' "$file"
    index=$((index + 1))
  done
  shopt -s nullglob
  for diagram in "$tmp_dir"/*.mmd; do
    [[ -s "$diagram" ]] || continue
    if [[ -f /usr/local/share/puppeteer-no-sandbox.json ]]; then
      mmdc -p /usr/local/share/puppeteer-no-sandbox.json -i "$diagram" -o "$diagram.svg" >/dev/null
    else
      mmdc -i "$diagram" -o "$diagram.svg" >/dev/null
    fi
  done
fi

echo "markdown lint ok"

