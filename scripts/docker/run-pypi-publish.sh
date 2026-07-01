#!/usr/bin/env bash
# PyPI publish on tag (runs in pypi-publish container; needs secrets on host env).
set -euo pipefail
cd /repo
pip install --quiet -e .
chmod +x scripts/pypi/*.sh scripts/docker/run-release.sh
./scripts/pypi/release.sh
