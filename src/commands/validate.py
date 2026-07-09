from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch

validate_app = typer.Typer(help="Validate repository data contracts.", no_args_is_help=True)


@validate_app.command("tasks")
def validate_tasks_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    dispatch("validate", "tasks", path)
