#!/usr/bin/env python3
"""Dockerized integration: every public cli CLI command (Typer endpoints + docker)."""
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
from gardusig_cli.integration.public_commands import (  # noqa: E402
    public_command_check_count,
    run_all_public_command_checks,
)
from gardusig_cli.integration.public_endpoints import prepare_git_repo  # noqa: E402


def main() -> int:
    require_docker_integration(context="check_public_commands.py")
    git_dir = integration_temp_dir("cli-public-")
    errors: list[str] = []
    try:
        prepare_git_repo(git_dir)
        errors = run_all_public_command_checks(ROOT, git_root=git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    if errors:
        print("Public command integration failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    count = public_command_check_count()
    print(f"Public command integration passed ({count} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
