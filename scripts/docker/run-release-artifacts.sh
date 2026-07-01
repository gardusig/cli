#!/usr/bin/env bash
# Release artifacts — build wheel/sdist into /artifacts (runs in release container).
set -euo pipefail
cd /repo
pip install --quiet -e .
chmod +x scripts/pypi/*.sh
version="${GITHUB_REF_NAME#v}"
export CLI_RELEASE_VERSION="${version}"
./scripts/pypi/build.sh
mkdir -p /artifacts
cp -a dist/* /artifacts/
