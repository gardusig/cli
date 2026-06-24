#!/usr/bin/env bash
# Shared helpers for install-pypi.sh and install.sh (host global cli on PATH).
set -euo pipefail

CLI_INSTALL_DEST="${CLI_INSTALL_DIR:-$HOME/.local/bin}"
PATH_MARKER='# cli (gardusig-cli)'
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

find_python312() {
  local candidate ver major minor
  if [[ -n "${PYTHON:-}" ]] && command -v "$PYTHON" >/dev/null 2>&1; then
    printf '%s\n' "$PYTHON"
    return 0
  fi
  for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      ver="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
      major="${ver%%.*}"
      minor="${ver#*.}"
      if [[ "$major" -ge 3 && "$minor" -ge 12 ]]; then
        printf '%s\n' "$candidate"
        return 0
      fi
    fi
  done
  echo "ERROR: Python 3.12+ not found (install via Homebrew: brew install python@3.12)" >&2
  return 1
}

ensure_cli_path_in_profile() {
  local profile="$1"
  [[ -f "$profile" ]] || return 0
  if grep -qF '.local/bin' "$profile" 2>/dev/null; then
    return 0
  fi
  {
    echo ""
    echo "$PATH_MARKER"
    echo "$PATH_LINE"
  } >>"$profile"
  echo "Added ~/.local/bin to PATH in $profile"
}

install_cli_path_hint() {
  echo ""
  echo "Open a new terminal (or run: source ~/.zprofile) then try: cli --help"
}

verify_cli_binary() {
  local bin="$1"
  if ! "$bin" --version >/dev/null 2>&1; then
    echo "ERROR: install verification failed — $bin --version" >&2
    return 1
  fi
}

remove_stale_binaries() {
  local dest="$1"
  if [[ -f "$dest/shuttle" ]]; then
    rm -f "$dest/shuttle"
  fi
}

ensure_cli_path_in_all_profiles() {
  ensure_cli_path_in_profile "$HOME/.zprofile"
  ensure_cli_path_in_profile "$HOME/.zshrc"
  ensure_cli_path_in_profile "$HOME/.bash_profile"
}
