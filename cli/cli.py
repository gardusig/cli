from __future__ import annotations

import typer

from cli import __version__
from cli.commands.backup import backup_app
from cli.commands.bookmarks import bookmarks_app
from cli.commands.chrome import chrome_app
from cli.commands.contest import contest_app
from cli.commands.docker import docker_app
from cli.commands.drive import drive_app
from cli.commands.gh import gh_app
from cli.commands.git import git_app
from cli.commands.links import links_app
from cli.commands.notion import notion_app
from cli.commands.publish import publish_app
from cli.commands.restore import restore_app
from cli.utils.logger import setup_logging

app = typer.Typer(
    name="cli",
    help="Git shortcuts and drive (tag zips) for macOS. Run `cli links` for docs and scripts.",
    no_args_is_help=True,
)

app.add_typer(links_app, name="links")
app.add_typer(git_app, name="git")
app.add_typer(gh_app, name="gh")
app.add_typer(backup_app, name="backup", hidden=True)
app.add_typer(restore_app, name="restore")
app.add_typer(drive_app, name="drive")
app.add_typer(notion_app, name="notion")
app.add_typer(chrome_app, name="chrome")
app.add_typer(bookmarks_app, name="bookmarks", hidden=True)
app.add_typer(docker_app, name="docker")
app.add_typer(contest_app, name="contest")
app.add_typer(publish_app, name="publish")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    setup_logging(verbose=verbose)
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None and not version:
        typer.echo(ctx.get_help())
        typer.echo("\nFull index: cli links  |  docs/README.md")
        raise typer.Exit()
    ctx.obj = {"verbose": verbose}


def run() -> None:
    """CLI entrypoint — surfaces ExternalCallError as a clean user message."""
    from cli.utils.config import load_local_env
    from cli.utils.external_client import ExternalCallError

    load_local_env()
    try:
        app()
    except ExternalCallError as exc:
        typer.echo(exc.user_message, err=True)
        raise typer.Exit(1) from exc


# Short alias: cli g <cmd> == cli git <cmd>
app.add_typer(git_app, name="g", hidden=True)
