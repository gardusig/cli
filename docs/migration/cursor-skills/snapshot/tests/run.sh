#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

bash "$TESTS_DIR/check-public-skills.sh"
python3 "$TESTS_DIR/check-public-skill-routing-descriptions.py"
python3 "$TESTS_DIR/check-public-skill-dag.py"
python3 "$TESTS_DIR/check-read-write-command-ownership.py"
python3 "$TESTS_DIR/check-shuttle-only-cli.py"
bash "$TESTS_DIR/check-write-skills-keywords.sh"
bash "$TESTS_DIR/check-skill-names.sh"
bash "$TESTS_DIR/check-no-internal-prefix.sh"
python3 "$TESTS_DIR/check-public-invoke-names.py"
python3 "$TESTS_DIR/check-stale-skill-refs.py"
python3 "$TESTS_DIR/check-structured-qa-shape.py"
python3 "$TESTS_DIR/check-public-no-qa-orchestration.py"
python3 "$TESTS_DIR/check-public-skip-env.py"
python3 "$TESTS_DIR/check-skill-suggestions-catalog.py"

echo "All skill checks passed."
