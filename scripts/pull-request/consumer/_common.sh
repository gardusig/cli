#!/usr/bin/env bash
# Shared helpers for post-install consumer integration (pip-installed cli binary only).
set -euo pipefail

consumer_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

consumer_index_has_version() {
  local package="$1"
  local version="$2"
  local index="${3:-testpypi}"
  local url
  if [[ "$index" == "pypi" ]]; then
    url="https://pypi.org/pypi/${package}/json"
  else
    url="https://test.pypi.org/pypi/${package}/json"
  fi
  response="$(curl -fsS "$url" 2>/dev/null || true)"
  [[ -n "$response" ]] && printf '%s' "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
version = sys.argv[1]
releases = data.get('releases') or {}
files = releases.get(version) or []
sys.exit(0 if files else 1)
" "$version"
}

consumer_wait_for_index() {
  local package="$1"
  local version="$2"
  local index="${3:-testpypi}"
  local attempts="${4:-12}"
  local delay="${5:-5}"
  local attempt=1
  while (( attempt <= attempts )); do
    if consumer_index_has_version "$package" "$version" "$index"; then
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
  local attempts="${CONSUMER_INSTALL_ATTEMPTS:-24}"
  local delay="${CONSUMER_INSTALL_DELAY:-5}"
  local attempt=1
  local -a pip_args
  if [[ "$index" == "pypi" ]]; then
    pip_args=(pip install --no-cache-dir "gardusig-cli==${version}")
  else
    pip_args=(
      pip install --no-cache-dir
      --index-url https://test.pypi.org/simple/
      --extra-index-url https://pypi.org/simple/
      "gardusig-cli==${version}"
    )
  fi
  while (( attempt <= attempts )); do
    if consumer_index_has_version "gardusig-cli" "$version" "$index"; then
      if "${pip_args[@]}"; then
        return 0
      fi
      echo "index lists gardusig-cli==${version} on ${index} but pip install failed (${attempt}/${attempts})"
    else
      echo "waiting for gardusig-cli==${version} on ${index} (${attempt}/${attempts})..."
    fi
    sleep "$delay"
    attempt=$((attempt + 1))
  done
  echo "failed to install gardusig-cli==${version} from ${index}" >&2
  return 1
}
