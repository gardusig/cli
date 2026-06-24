#!/usr/bin/env bash
# Install cli from PyPI into ~/.local/share/gardusig-cli (latest release by default).
# Use from any machine — no repo clone required. Config: ~/.config/cli/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_install_common.sh
source "$SCRIPT_DIR/_install_common.sh"

PACKAGE="gardusig-cli"
INSTALL_HOME="${CLI_INSTALL_HOME:-$HOME/.local/share/gardusig-cli}"
VENV="$INSTALL_HOME/venv"
DEST="$CLI_INSTALL_DEST"
PIN_VERSION="${CLI_INSTALL_VERSION:-}"
UPGRADE=1

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install or upgrade gardusig-cli from PyPI into $INSTALL_HOME.
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

spec="$PACKAGE"
if [[ -n "$PIN_VERSION" ]]; then
  spec="${PACKAGE}==${PIN_VERSION#v}"
  echo "==> Installing $spec from PyPI"
  pip install -q "$spec"
else
  echo "==> Installing latest $PACKAGE from PyPI"
  if [[ "$UPGRADE" == "1" ]]; then
    pip install --upgrade -q "$PACKAGE"
  else
    pip install -q "$PACKAGE"
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
echo "Package:   $PACKAGE"
echo "Version:   $installed_version"
echo "Venv:      $VENV"
echo "Config:    ~/.config/cli/  (override with CLI_CONFIG_DIR)"
install_cli_path_hint
