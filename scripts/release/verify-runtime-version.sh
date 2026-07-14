#!/usr/bin/env bash
# Ensure gardusig-cli inside the runtime image matches the Docker/PyPI version tag.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

expected="${CLI_VERSION:?CLI_VERSION required}"
if [[ -n "${RUNTIME_IMAGE:-}" ]]; then
  got="$(docker run --rm "${RUNTIME_IMAGE}:${expected}" --version)"
else
  got="$(cli --version)"
fi
if [[ "$got" != "$expected" ]]; then
  echo "runtime version mismatch: docker/pypi tag ${expected}, cli --version ${got}" >&2
  exit 1
fi
echo "runtime version ok: ${expected}"
