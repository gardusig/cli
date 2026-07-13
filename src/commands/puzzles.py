"""Static puzzle manifest helpers."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

puzzles_app = typer.Typer(help="Validate static puzzle manifests.", no_args_is_help=True)


@puzzles_app.command("validate")
def validate_manifest_cmd(
    manifest: Path = typer.Option(Path("games.yaml"), "--manifest"),
) -> None:
    """Validate a puzzles YAML manifest."""
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    items = data.get("games") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise typer.BadParameter("manifest must contain a list or games: list")
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("id") or "").strip()
        if title:
            count += 1
    typer.echo(f"ok: {count} entries in {manifest}")
