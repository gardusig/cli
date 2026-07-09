#!/usr/bin/env bash
# Shared helpers for post-install consumer integration (pip-installed cli binary only).
set -euo pipefail

consumer_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

consumer_wait_for_index() {
  local package="$1"
  local version="$2"
  local index="${3:-testpypi}"
  local attempts="${4:-12}"
  local delay="${5:-5}"
  local url
  if [[ "$index" == "pypi" ]]; then
    url="https://pypi.org/pypi/${package}/json"
  else
    url="https://test.pypi.org/pypi/${package}/json"
  fi
  local attempt=1
  while (( attempt <= attempts )); do
    if response="$(curl -fsS "$url" 2>/dev/null)" && [[ -n "$response" ]] && printf '%s' "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
version = sys.argv[1]
releases = data.get('releases') or {}
sys.exit(0 if version in releases and releases[version] else 1)
" "$version"; then
      return 0
    fi
    echo "waiting for ${package}==${version} on ${index} (${attempt}/${attempts})..."
    sleep "$delay"
    attempt=$((attempt + 1))
  done
  echo "timed out waiting for ${package}==${version} on ${index}" >&2
  return 1
}

consumer_install_package() {
  local version="${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION is required}"
  local index="${PYPI_INDEX:-testpypi}"
  consumer_wait_for_index "gardusig-cli" "$version" "$index"
  if [[ "$index" == "pypi" ]]; then
    pip install --no-cache-dir "gardusig-cli==${version}"
  else
    pip install --no-cache-dir \
      --index-url https://test.pypi.org/simple/ \
      --extra-index-url https://pypi.org/simple/ \
      "gardusig-cli==${version}"
  fi
}
