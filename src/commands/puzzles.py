"""Static puzzle repository helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
import yaml

puzzles_app = typer.Typer(help="Manage static-puzzles repository tasks.", no_args_is_help=True)
issues_app = typer.Typer(help="GitHub issue helpers for puzzles.", no_args_is_help=True)
puzzles_app.add_typer(issues_app, name="issues")


@issues_app.command("create")
def create_issues_cmd(
    manifest: Path = typer.Option(Path("games.yaml"), "--manifest"),
    repo: str = typer.Option("gardusig/static-puzzles", "--repo"),
    dry_run: bool = typer.Option(True, "--dry-run/--yes"),
) -> None:
    """Create one GitHub issue per puzzle/game entry in a YAML manifest."""
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    items = data.get("games") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise typer.BadParameter("manifest must contain a list or games: list")
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("id") or "").strip()
        if not title:
            continue
        body = str(item.get("description") or "Generated from static-puzzles manifest.")
        if dry_run:
            typer.echo(f"DRY-RUN issue: {title}")
            continue
        subprocess.run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body],
            check=True,
        )
