#!/usr/bin/env bash
# Shared helpers for per-package test scripts (raw shell — no cli, no python3 -m src).
set -euo pipefail

repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

_package_unit_paths() {
  case "$1" in
    gh) echo "tests/gh/ tests/harness/gh_harness.py" ;;
    git) echo "tests/git/" ;;
    notion) echo "tests/notion/" ;;
    drive) echo "tests/drive/ tests/backup/ tests/providers/test_google_drive.py tests/providers/test_onedrive.py" ;;
    chrome) echo "tests/chrome/ tests/harness/chrome_harness.py" ;;
    docker) echo "tests/docker/" ;;
    contest) echo "tests/contest/" ;;
    project) echo "tests/project/ tests/cli/test_project_command.py" ;;
    pypi) echo "tests/pypi/ tests/cli/test_release_commands.py" ;;
    *)
      echo "unknown package: $1" >&2
      return 1
      ;;
  esac
}

_run_integration_check() {
  local package="$1"
  local check="$2"
  case "$check" in
    package-integration)
      python3 tests/integration/check_package_integration.py --package "$package"
      ;;
    "tests/integration/check_docker_commands.py")
      python3 tests/integration/check_docker_commands.py
      ;;
    *)
      if [[ "$check" == *"--help" ]] || [[ "$check" == "languages list" ]]; then
        return 0
      fi
      echo "skip unsupported integration check: $check" >&2
      ;;
  esac
}

_package_integration_checks() {
  case "$1" in
    gh|git|notion|drive|chrome|contest|project|pypi) echo "package-integration" ;;
    docker) echo "package-integration tests/integration/check_docker_commands.py" ;;
    *) echo "" ;;
  esac
}

run_package() {
  local package="$1"
  shift
  local include_unit=1
  local include_integration=1
  local dry_run=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --no-unit) include_unit=0; shift ;;
      --no-integration) include_integration=0; shift ;;
      --dry-run) dry_run=1; shift ;;
      *) break ;;
    esac
  done

  local root
  root="$(repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-config/ci}"
  export CLI_DOCKER_INTEGRATION="${CLI_DOCKER_INTEGRATION:-1}"
  export CLI_ROOT="$root"
  cd "$root"

  if (( include_unit )); then
    read -r -a unit_paths <<< "$(_package_unit_paths "$package")"
    if (( dry_run )); then
      printf 'pytest -q %s\n' "${unit_paths[*]}"
    else
      python3 -m pytest -q "${unit_paths[@]}"
    fi
  fi

  if (( include_integration )); then
    read -r -a checks <<< "$(_package_integration_checks "$package")"
    for check in "${checks[@]}"; do
      if (( dry_run )); then
        echo "integration: $check"
      else
        _run_integration_check "$package" "$check"
      fi
    done
  fi
}
