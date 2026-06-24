#!/usr/bin/env bash
# PR gate: build gardusig-cli 1.0.0 and optionally upload to TestPyPI (TESTPYPI_API_TOKEN).
set -euo pipefail
export CLI_DOCKER_TARGET="${CLI_DOCKER_TARGET:-integration}"
export CLI_DOCKER_IMAGE="${CLI_DOCKER_IMAGE:-cli:integration}"
# shellcheck source=docker/common.sh
source "$(dirname "$0")/docker/common.sh"

TEST_VERSION="${CLI_PYPI_TEST_VERSION:-1.0.0}"
SKIP_EXISTING="${CLI_PYPI_SKIP_EXISTING:-1}"

INNER="$(docker_copy_workspace_script)
set -euo pipefail
cd '$CONTAINER_WORK'
export CLI_RELEASE_VERSION='$TEST_VERSION'
export CLI_PYPI_TEST=0
export CLI_PYPI_SKIP_EXISTING='$SKIP_EXISTING'

echo '==> pypi build (version $TEST_VERSION)'
./scripts/pypi/build.sh

echo '==> verify artifacts'
ls -la dist/
if ! ls dist/*'$TEST_VERSION'* >/dev/null 2>&1; then
  echo 'ERROR: dist/ missing artifacts for version $TEST_VERSION' >&2
  exit 1
fi

if [[ -n \"\${TESTPYPI_API_TOKEN:-}\" ]]; then
  echo '==> testpypi upload'
  export PYPI_API_TOKEN=\"\$TESTPYPI_API_TOKEN\"
  export CLI_PYPI_TEST=1
  ./scripts/pypi/upload.sh
  echo '==> verify TestPyPI project page'
  python -c \"
from cli.services.pypi_publish import PACKAGE_NAME, verify_package_version_on_index
verify_package_version_on_index(PACKAGE_NAME, '$TEST_VERSION', testpypi=True)
print('Verified', PACKAGE_NAME + '==$TEST_VERSION', 'on TestPyPI')
\"
else
  echo '==> skip TestPyPI upload (TESTPYPI_API_TOKEN not set)'
fi
"

docker_run_in_workspace "$INNER"
