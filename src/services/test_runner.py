"""Python-backed test runners for the CLI package."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_unit(root: Path) -> None:
    subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "-m",
            "not integration",
            "--cov=src",
            "--cov-config=coverage-unit.ini",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
        ],
        cwd=root,
        check=True,
    )


def run_integration(root: Path) -> None:
    subprocess.run(["bash", "scripts/pull-request/integration-test.sh"], cwd=root, check=True)


def run_command_surface(root: Path) -> None:
    subprocess.run(["bash", "scripts/pull-request/integration-smoke.sh"], cwd=root, check=True)
