"""Test pipeline commands."""

from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch
test_app = typer.Typer(help="Run repo test pipeline (unit / integration / all).", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


@test_app.command("python")
def test_python_cmd(
    suite: str = typer.Argument(..., help="Suite: unit, integration, command-surface."),
    path: Path = typer.Argument(Path("."), help="Repository root."),
) -> None:
    dispatch("test", "python", path, suite=suite)


@test_app.command("typescript")
def test_typescript_cmd(
    suite_or_path: str = typer.Argument("unit", help="Suite or repository path."),
    path: Path | None = typer.Argument(None, help="Repository root."),
) -> None:
    if suite_or_path in {"unit", "build"}:
        suite = suite_or_path
        workspace = path or Path(".")
    else:
        suite = "unit"
        workspace = Path(suite_or_path)
    dispatch("test", "typescript", workspace, suite=suite)


@test_app.command("cpp")
def test_cpp_cmd(
    suite: str = typer.Argument(..., help="Suite: compile, smoke."),
    path: Path = typer.Argument(Path("."), help="Repository root."),
) -> None:
    dispatch("test", "cpp", path, suite=suite)


@test_app.command("java")
def test_java_cmd(
    suite: str = typer.Argument(..., help="Suite: unit."),
    path: Path = typer.Argument(Path("."), help="Repository root."),
) -> None:
    dispatch("test", "java", path, suite=suite)


@test_app.command("unit", hidden=True)
def test_unit_cmd() -> None:
    dispatch("test", "python", _ROOT, suite="unit")


@test_app.command("integration", hidden=True)
def test_integration_cmd() -> None:
    dispatch("test", "python", _ROOT, suite="integration")


@test_app.command("command-surface", hidden=True)
def test_command_surface_cmd() -> None:
    dispatch("test", "python", _ROOT, suite="command-surface")


@test_app.command("regression", hidden=True)
def test_regression_cmd() -> None:
    dispatch("test", "python", _ROOT, suite="unit")
    dispatch("test", "python", _ROOT, suite="integration")


@test_app.command("all", hidden=True)
def test_all_cmd() -> None:
    dispatch("test", "python", _ROOT, suite="unit")
    dispatch("test", "python", _ROOT, suite="integration")
