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
    checks = [
        ["python", "tests/integration/check_integration_coverage.py"],
        ["python", "tests/integration/check_public_commands.py"],
        ["python", "tests/integration/check_workflow_integration.py"],
        ["python", "tests/integration/check_api_integration.py"],
    ]
    for cmd in checks:
        subprocess.run(cmd, cwd=root, check=True)
    subprocess.run(["python", "-m", "pytest", "-q", "-m", "integration"], cwd=root, check=True)


def run_command_surface(root: Path) -> None:
    subprocess.run(["python", "tests/integration/check_public_commands.py"], cwd=root, check=True)
