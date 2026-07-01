from __future__ import annotations

import typer

from src import __version__
from src.commands.opencode_cmd import opencode_app
from src.commands.ai import ai_app
from src.commands.backup import backup_app
from src.commands.bookmarks import bookmarks_app
from src.commands.chrome import chrome_app
from src.commands.contest import contest_app
from src.commands.deploy_cmd import deploy_app
from src.commands.chat import chat_app
from src.commands.craft import craft_app
from src.commands.docker import docker_app
from src.commands.drive import drive_app
from src.commands.gh import gh_app
from src.commands.git import git_app
from src.commands.links import links_app
from src.commands.notion import notion_app
from src.commands.pypi import pypi_app
from src.commands.publish import publish_app
from src.commands.release_cmd import release_app
from src.commands.restore import restore_app
from src.commands.review import review_app
from src.commands.test_cmd import test_app
from src.utils.logger import setup_logging

app = typer.Typer(
    name="cli",
    help="Git shortcuts and drive (tag zips) for macOS. Run `cli links` for docs and scripts.",
    no_args_is_help=True,
)

app.add_typer(links_app, name="links")
app.add_typer(git_app, name="git")
app.add_typer(gh_app, name="gh")
app.add_typer(opencode_app, name="opencode")
app.add_typer(ai_app, name="ai", hidden=True)
app.add_typer(chat_app, name="chat", hidden=True)
app.add_typer(craft_app, name="craft", hidden=True)
app.add_typer(review_app, name="review", hidden=True)
app.add_typer(test_app, name="test")
app.add_typer(deploy_app, name="deploy")
app.add_typer(release_app, name="release")
app.add_typer(backup_app, name="backup", hidden=True)
app.add_typer(restore_app, name="restore")
app.add_typer(drive_app, name="drive")
app.add_typer(notion_app, name="notion")
app.add_typer(chrome_app, name="chrome")
app.add_typer(bookmarks_app, name="bookmarks", hidden=True)
app.add_typer(docker_app, name="docker")
app.add_typer(contest_app, name="contest")
app.add_typer(pypi_app, name="pypi")
app.add_typer(publish_app, name="publish", hidden=True)


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
    from src.services.gh_policy import GhPolicyError
    from src.utils.config import load_local_env
    from src.utils.external_client import ExternalCallError

    load_local_env()
    try:
        app()
    except ExternalCallError as exc:
        typer.echo(exc.user_message, err=True)
        raise typer.Exit(1) from exc
    except GhPolicyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


# Short alias: cli g <cmd> == cli git <cmd>
app.add_typer(git_app, name="g", hidden=True)
