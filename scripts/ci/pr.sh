#!/usr/bin/env bash
# PR publish path: version gate → unit coverage → TestPyPI upload.
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$dir/version-check.sh"
bash "$dir/unit-test.sh"
bash "$dir/pypi-test.sh"
