#!/usr/bin/env bash
set -euo pipefail
# Create a GitHub release manually in the browser or with your own tooling.
# This CLI publishes tags via `cli release main` (git tag + push + PyPI).

tag="${RELEASE_TAG:?RELEASE_TAG required}"
version="${CLI_VERSION:?CLI_VERSION required}"

echo "Tag ${tag} should already be pushed. Create the GitHub release for gardusig-cli ${version} in the repository UI."
