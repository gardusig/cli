"""Hidden legacy alias: `cli bookmarks` → `cli chrome bookmarks`."""

from __future__ import annotations

import typer

from cli.commands.chrome import bookmarks_deploy_to_chrome, bookmarks_ingest_from_chrome

bookmarks_app = typer.Typer(help="(deprecated) use cli chrome bookmarks", hidden=True)


@bookmarks_app.command("export")
def legacy_export() -> None:
    """Deprecated: remote-centric Chrome→local; use `cli chrome bookmarks ingest`."""
    bookmarks_ingest_from_chrome()


@bookmarks_app.command("import")
def legacy_import() -> None:
    """Deprecated: remote-centric local→Chrome; use `cli chrome bookmarks deploy`."""
    bookmarks_deploy_to_chrome()
