#!/usr/bin/env python3
"""Integration check: end-to-end workflow scenarios (plan, context, pr, reset)."""
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
from src.integration.public_endpoints import prepare_git_repo  # noqa: E402
from src.integration.workflows import WORKFLOW_REGISTRY, run_all_workflow_e2e_checks  # noqa: E402


def main() -> int:
    require_docker_integration(context="check_workflows.py")
    git_dir = integration_temp_dir("cli-workflow-e2e-")
    errors: list[str] = []
    try:
        prepare_git_repo(git_dir)
        errors = run_all_workflow_e2e_checks(ROOT, git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    if errors:
        print("Workflow E2E integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = len(WORKFLOW_REGISTRY)
    print(f"Workflow E2E integration passed ({count} workflows).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
