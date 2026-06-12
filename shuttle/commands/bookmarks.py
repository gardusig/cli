"""Hidden legacy alias: `shuttle bookmarks` → `shuttle chrome bookmarks`."""

from __future__ import annotations

import typer

from shuttle.commands.chrome import bookmarks_deploy_to_chrome, bookmarks_ingest_from_chrome

bookmarks_app = typer.Typer(help="(deprecated) use shuttle chrome bookmarks", hidden=True)


@bookmarks_app.command("export")
def legacy_export() -> None:
    """Deprecated: remote-centric Chrome→local; use `shuttle chrome bookmarks ingest`."""
    bookmarks_ingest_from_chrome()


@bookmarks_app.command("import")
def legacy_import() -> None:
    """Deprecated: remote-centric local→Chrome; use `shuttle chrome bookmarks deploy`."""
    bookmarks_deploy_to_chrome()
