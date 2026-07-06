#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/toolkit/_common.sh"

java_build_tool() {
  if [[ -f pom.xml ]] && command -v mvn >/dev/null 2>&1; then
    printf '%s\n' "mvn"
    return 0
  fi
  if [[ ( -f build.gradle || -f build.gradle.kts ) && -x ./gradlew ]]; then
    printf '%s\n' "./gradlew"
    return 0
  fi
  if [[ ( -f build.gradle || -f build.gradle.kts ) ]] && command -v gradle >/dev/null 2>&1; then
    printf '%s\n' "gradle"
    return 0
  fi
  echo "ERROR: Java project requires Maven or Gradle" >&2
  return 1
}

