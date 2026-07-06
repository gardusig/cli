"""Wiki synchronization commands."""

from __future__ import annotations

from pathlib import Path

import typer

from src.services.repo_inventory import sync_wiki_repositories

wiki_app = typer.Typer(help="Sync generated wiki pages.", no_args_is_help=True)
repos_app = typer.Typer(help="Repository inventory sync.", no_args_is_help=True)
wiki_app.add_typer(repos_app, name="repos")


@repos_app.command("sync")
def repos_sync_cmd(
    wiki_dir: Path = typer.Option(Path("."), "--wiki-dir", help="Local gardusig/wiki checkout."),
    owner: str = typer.Option("gardusig", "--owner"),
    ref: str = typer.Option("main", "--ref"),
    depth: int = typer.Option(3, "--depth", min=1, max=6),
    include_private: bool = typer.Option(True, "--include-private/--public-only"),
) -> None:
    """Write repositories/*.md inventory pages into a wiki checkout."""
    written = sync_wiki_repositories(
        wiki_dir.expanduser(),
        owner=owner,
        ref=ref,
        depth=depth,
        include_private=include_private,
    )
    typer.echo(f"updated {len(written)} repository inventory page(s)")
