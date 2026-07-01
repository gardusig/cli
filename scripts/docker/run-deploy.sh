#!/usr/bin/env bash
# Deploy gate — tag main when ahead of latest tag (runs in deploy container).
set -euo pipefail
cd /repo
git config --global --add safe.directory /repo
pip install --quiet -e .
chmod +x scripts/git/deploy.sh
./scripts/git/deploy.sh --yes
