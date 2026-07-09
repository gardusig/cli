"""Commands for gardusig/private validation."""

from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch

database_app = typer.Typer(help="Validate gardusig/private data.", no_args_is_help=True)


@database_app.command("validate-pr")
def validate_pr_cmd(
    path: Path = typer.Argument(Path("."), help="Database repo root."),
    base: str = typer.Option("main", "--base"),
) -> None:
    """Hidden compatibility alias for `cli validate vault`."""
    dispatch("validate", "vault", path, extra_env={"BASE": base})
