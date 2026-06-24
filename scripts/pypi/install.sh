#!/usr/bin/env bash
# Install gardusig-cli from PyPI into ~/.local/share/gardusig-cli (latest by default).
# Config after install: ~/.config/cli/
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

INSTALL_HOME="${CLI_INSTALL_HOME:-$HOME/.local/share/gardusig-cli}"
VENV="$INSTALL_HOME/venv"
DEST="${CLI_INSTALL_DIR:-$HOME/.local/bin}"
PATH_MARKER='# cli (gardusig-cli)'
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
PIN_VERSION="${CLI_INSTALL_VERSION:-}"
UPGRADE=1

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

ensure_cli_path_in_all_profiles() {
  ensure_cli_path_in_profile "$HOME/.zprofile"
  ensure_cli_path_in_profile "$HOME/.zshrc"
  ensure_cli_path_in_profile "$HOME/.bash_profile"
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

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install or upgrade $PACKAGE_NAME from PyPI into $INSTALL_HOME.
Places the cli command in $DEST and adds ~/.local/bin to your shell PATH.

Options:
  --version VER   Install an exact version (default: latest on PyPI)
  --no-upgrade    Skip pip --upgrade when re-running install
  -h, --help      Show this help

Environment:
  CLI_INSTALL_HOME     Venv parent directory (default: ~/.local/share/gardusig-cli)
  CLI_INSTALL_DIR      Destination for cli binary (default: ~/.local/bin)
  CLI_INSTALL_VERSION  Same as --version
  PYTHON               Python 3.12+ executable
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    --version)
      [[ $# -ge 2 ]] || {
        echo "ERROR: --version requires a value" >&2
        exit 1
      }
      PIN_VERSION="$2"
      shift 2
      ;;
    --no-upgrade)
      UPGRADE=0
      shift
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

PYTHON_BIN="$(find_python312)"
mkdir -p "$DEST" "$INSTALL_HOME"

if [[ ! -d "$VENV" ]]; then
  echo "==> Creating venv at $VENV"
  "$PYTHON_BIN" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -U pip -q

if [[ -n "$PIN_VERSION" ]]; then
  spec="${PACKAGE_NAME}==${PIN_VERSION#v}"
  echo "==> Installing $spec from PyPI"
  pip install -q "$spec"
else
  echo "==> Installing latest $PACKAGE_NAME from PyPI"
  if [[ "$UPGRADE" == "1" ]]; then
    pip install --upgrade -q "$PACKAGE_NAME"
  else
    pip install -q "$PACKAGE_NAME"
  fi
fi

CLI_VENV_BIN="$VENV/bin/cli"
if [[ ! -x "$CLI_VENV_BIN" ]]; then
  echo "ERROR: $CLI_VENV_BIN not found after pip install" >&2
  exit 1
fi

ln -sf "$CLI_VENV_BIN" "$DEST/cli"
remove_stale_binaries "$DEST"
ensure_cli_path_in_all_profiles
verify_cli_binary "$DEST/cli"

installed_version="$("$DEST/cli" --version)"
echo ""
echo "Installed: $DEST/cli"
echo "Package:   $PACKAGE_NAME"
echo "Version:   $installed_version"
echo "Venv:      $VENV"
echo "Config:    ~/.config/cli/  (override with CLI_CONFIG_DIR)"
echo ""
echo "Open a new terminal (or run: source ~/.zprofile) then try: cli --help"
