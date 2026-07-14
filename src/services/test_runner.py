"""Python-backed test runners for the CLI package."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.services.cli_smoke import SmokeError, run_all as run_smoke


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
    try:
        run_smoke(workspace=root)
    except SmokeError as exc:
        raise RuntimeError(str(exc)) from exc


def run_command_surface(root: Path) -> None:
    run_integration(root)
