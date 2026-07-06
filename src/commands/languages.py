from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch

languages_app = typer.Typer(help="Discover supported toolkit languages.", no_args_is_help=True)


@languages_app.command("list")
def languages_list_cmd(path: Path = typer.Argument(Path("."), help="Repository root.")) -> None:
    dispatch("languages", "list", path)


@languages_app.command("show")
def languages_show_cmd(
    language: str = typer.Argument(..., help="Language name."),
    path: Path = typer.Argument(Path("."), help="Repository root."),
) -> None:
    dispatch("languages", "show", path, extra_env={"CLI_LANGUAGE": language})

