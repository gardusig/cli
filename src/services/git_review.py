"""Workspace health checks."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.utils.config import project_root


def run_review(*, install: bool = True, quick: bool = False) -> int:
    """Run lightweight command checks; full mode runs the Python unit test CLI gate."""
    root = project_root()
    _ = install

    subprocess.run(["cli", "test", "python", "command-surface", str(root)], cwd=root, check=True)

    if quick:
        return 0

    result = subprocess.run(["cli", "test", "python", "unit", str(root)], cwd=root)
    return result.returncode
