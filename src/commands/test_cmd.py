"""Test pipeline commands — wrap scripts/test/*.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

test_app = typer.Typer(help="Run repo test pipeline (unit / integration / all).", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


def _run(script: str) -> None:
    path = _ROOT / script
    if not path.is_file():
        raise typer.BadParameter(f"Missing script: {path}")
    subprocess.run(["bash", str(path)], cwd=_ROOT, check=True)


@test_app.command("unit")
def test_unit_cmd() -> None:
    _run("scripts/test/unit.sh")


@test_app.command("integration")
def test_integration_cmd() -> None:
    _run("scripts/test/integration.sh")


@test_app.command("all")
def test_all_cmd() -> None:
    _run("scripts/test/all.sh")
