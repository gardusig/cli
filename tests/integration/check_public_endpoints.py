#!/usr/bin/env python3
"""Integration check: invoke every public cli CLI endpoint."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gardusig_cli.integration.docker_guard import (  # noqa: E402
    cleanup_integration_temp_dir,
    integration_temp_dir,
    require_docker_integration,
)
from gardusig_cli.integration.public_endpoints import (  # noqa: E402
    endpoint_checks,
    prepare_git_repo,
    run_all_endpoint_checks,
)


def main() -> int:
    require_docker_integration(context="check_public_endpoints.py")
    git_dir = integration_temp_dir("cli-git-")
    errors: list[str] = []
    try:
        prepare_git_repo(git_dir)
        errors = run_all_endpoint_checks(ROOT, git_root=git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    if errors:
        print("Public endpoint integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(endpoint_checks())
    print(f"Public endpoint integration passed ({count} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
