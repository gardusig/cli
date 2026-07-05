from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch

lint_app = typer.Typer(help="Run language and repo lint commands.", no_args_is_help=True)


def _lint(subject: str, path: Path) -> None:
    dispatch("lint", subject, path)


@lint_app.command("repo")
def lint_repo_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("repo", path)


@lint_app.command("markdown")
def lint_markdown_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("markdown", path)


@lint_app.command("python")
def lint_python_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("python", path)


@lint_app.command("typescript")
def lint_typescript_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("typescript", path)


@lint_app.command("cpp")
def lint_cpp_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("cpp", path)


@lint_app.command("shell")
def lint_shell_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("shell", path)


@lint_app.command("java")
def lint_java_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    _lint("java", path)

