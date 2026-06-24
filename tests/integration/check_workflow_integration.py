#!/usr/bin/env python3
"""Integration check: start, push, and reset workflow scenarios."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration.docker_guard import (  # noqa: E402
    cleanup_integration_temp_dir,
    integration_temp_dir,
    require_docker_integration,
)
from src.integration.workflow_integration import (  # noqa: E402
    WORKFLOW_CHECKS,
    prepare_workflow_git,
    run_all_workflow_checks,
)


def main() -> int:
    require_docker_integration(context="check_workflow_integration.py")
    git_dir = integration_temp_dir("cli-workflow-")
    errors: list[str] = []
    try:
        prepare_workflow_git(git_dir)
        errors = run_all_workflow_checks(ROOT, git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    if errors:
        print("Workflow integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(WORKFLOW_CHECKS)
    print(f"Workflow integration passed ({count} scenarios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
