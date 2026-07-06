"""Repository inventory commands."""

from __future__ import annotations

import json

import typer

from src.services.repo_inventory import inventory_repo, render_inventory_markdown

repo_app = typer.Typer(help="Inspect repository metadata from GitHub.", no_args_is_help=True)


@repo_app.command("inventory")
def inventory_cmd(
    repository: str = typer.Argument(..., help="Repository as owner/name."),
    ref: str = typer.Option("main", "--ref"),
    depth: int = typer.Option(3, "--depth", min=1, max=6),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Render deterministic repository inventory from the main branch tree."""
    inv = inventory_repo(repository, ref=ref, depth=depth)
    if json_output:
        typer.echo(json.dumps(inv, indent=2))
        return
    typer.echo(render_inventory_markdown(inv))
