"""Hidden aliases for legacy `cli backup` → use `cli drive` instead."""

from __future__ import annotations

import typer

from src.commands.drive import delete_cmd, ingest_cmd, list_cmd, status_cmd

backup_app = typer.Typer(
    help="(deprecated) use cli drive",
    no_args_is_help=True,
    hidden=True,
)
repository_app = typer.Typer(help="(deprecated)", hidden=True)


@backup_app.command("status")
def backup_status_alias() -> None:
    """Deprecated: use `cli drive status`."""
    status_cmd()


@repository_app.command("sync")
def repository_sync_alias(
    path: str | None = typer.Argument(None),
) -> None:
    """Deprecated: use `cli drive ingest`."""
    ingest_cmd(path)


@repository_app.command("list")
def repository_list_alias(
    path: str | None = typer.Argument(None),
) -> None:
    """Deprecated: use `cli drive list`."""
    list_cmd(path)


@repository_app.command("delete")
def repository_delete_alias(
    path: str = typer.Argument(...),
    tag: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Deprecated: use `cli drive delete`."""
    delete_cmd(path, tag, yes=yes)


backup_app.add_typer(repository_app, name="repository")
