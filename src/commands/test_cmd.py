"""Test pipeline commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import typer

from src.commands._toolkit import dispatch
from src.services.test_packages import (
    changed_paths_from_git,
    full_suite_payload,
    package_command_payload,
    package_resolution_payload,
    test_package_registry,
)

test_app = typer.Typer(help="Run repo test pipeline (unit / integration / all).", no_args_is_help=True)
packages_app = typer.Typer(help="Resolve changed paths to CLI test packages.", no_args_is_help=True)
test_app.add_typer(packages_app, name="packages")

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


@packages_app.command("resolve")
def test_packages_resolve_cmd(
    changed_path: list[str] | None = typer.Option(
        None,
        "--changed-path",
        "-p",
        help="Repo-relative changed path. Repeat for multiple paths.",
    ),
    base: str | None = typer.Option(None, "--base", help="Git base ref for changed path detection."),
    head: str | None = typer.Option(None, "--head", help="Git head ref for changed path detection."),
    path: Path = typer.Option(Path("."), "--path", help="Repository root for git diff detection."),
    package_limit: int = typer.Option(4, "--package-limit", help="Fallback to full suite above this package count."),
    format: str = typer.Option("json", "--format", help="json or table"),
) -> None:
    """Resolve changed files to focused CLI test packages."""
    _validate_format(format)
    paths = list(changed_path or [])
    if base or head:
        if not base or not head:
            typer.echo("Error: --base and --head must be provided together", err=True)
            raise typer.Exit(2)
        try:
            paths.extend(changed_paths_from_git(base, head, path))
        except RuntimeError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
    payload = package_resolution_payload(paths, package_limit=package_limit)
    if format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return
    typer.echo("packages: " + (", ".join(payload["package_names"]) or "(none)"))
    if payload["full_suite"]:
        typer.echo("full-suite: yes (" + "; ".join(payload["full_suite_reasons"]) + ")")
    for instruction in payload["instructions"]:
        typer.echo(f"- {instruction}")


@packages_app.command("list")
def test_packages_list_cmd(
    format: str = typer.Option("json", "--format", help="json or table"),
) -> None:
    """List the package registry for pipeline consumers."""
    _validate_format(format)
    payload = {
        "packages": [package.as_dict() for package in test_package_registry()],
    }
    if format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return
    for package in payload["packages"]:
        broad = " broad" if package["broad"] else ""
        typer.echo(f"{package['name']}{broad}: {' '.join(package['unit_test_paths'])}")


@packages_app.command("run")
def test_packages_run_cmd(
    package: str = typer.Argument(..., help="Package name from `cli test packages list`."),
    path: Path = typer.Option(Path("."), "--path", help="Repository root."),
    include_unit: bool = typer.Option(True, "--unit/--no-unit"),
    include_integration: bool = typer.Option(True, "--integration/--no-integration"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print command contract without running."),
    format: str = typer.Option("json", "--format", help="json or table for --dry-run output."),
) -> None:
    """Run or describe focused tests for one CLI package."""
    _validate_format(format)
    try:
        payload = package_command_payload(
            package,
            include_unit=include_unit,
            include_integration=include_integration,
        )
    except KeyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    if dry_run:
        _emit_payload(payload, format)
        return
    for command in payload["commands"]:
        env = os.environ | {key: str(value) for key, value in command["env"].items()}
        code = subprocess.run(command["command"], cwd=path, env=env, check=False).returncode
        if code != 0:
            raise typer.Exit(code)


@packages_app.command("suite")
def test_packages_suite_cmd(
    format: str = typer.Option("json", "--format", help="json or table"),
) -> None:
    """Describe the full-suite contract owned by github-pipelines."""
    _validate_format(format)
    _emit_payload(full_suite_payload(), format)


def _validate_format(format: str) -> None:
    if format not in {"json", "table"}:
        typer.echo("Error: --format expected one of: json, table", err=True)
        raise typer.Exit(2)


def _emit_payload(payload: dict, format: str) -> None:
    if format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return
    commands = payload.get("commands", [])
    if "package" in payload:
        typer.echo(f"package: {payload['package']['name']}")
    elif "packages" in payload:
        typer.echo("packages: " + ", ".join(payload["packages"]))
    for command in commands:
        typer.echo(f"{command['kind']}: " + " ".join(command["command"]))


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
