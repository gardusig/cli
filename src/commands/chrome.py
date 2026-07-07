"""Chrome browser integrations (bookmarks today; more later)."""

from __future__ import annotations

import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint

from src.services.bookmark_sync import (
    export_bookmarks,
    import_bookmarks,
    merge_bookmarks,
    newest_html_export,
    snapshot_bookmarks,
    wait_for_exported_html,
)
from src.services.photos_sync import ingest_takeout, list_albums, photos_status
from src.internal.write.gate import require_write_gate
from src.utils.config import (
    bookmarks_file_path,
    chrome_downloads_dir,
    chrome_profile_key,
    chrome_snapshot_retention,
    chrome_snapshots_dir,
    photos_dir_path,
    photos_takeout_dir,
    project_root,
)

chrome_app = typer.Typer(help="Chrome browser — bookmarks and photos integrations.", no_args_is_help=True)
bookmarks_app = typer.Typer(help="Bookmark ingest / deploy (local-centric).", no_args_is_help=True)
photos_app = typer.Typer(help="Google Photos Takeout ingest (file-based).", no_args_is_help=True)


class ChromeOutputFormat(str, Enum):
    table = "table"
    json = "json"


def _emit_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2))


def _resolve_source_path(source: str | None) -> Path | None:
    if not source:
        return None
    raw = Path(source).expanduser()
    return raw if raw.is_absolute() else project_root() / raw


def _resolve_merge_source(source: str | None, *, downloads_dir: Path) -> Path:
    explicit = _resolve_source_path(source)
    if explicit:
        return explicit
    if os.environ.get("CLI_SKIP_CHROME_AUTOMATION") == "1":
        found = newest_html_export(downloads_dir)
        if not found:
            raise FileNotFoundError(f"No HTML export in {downloads_dir}")
        return found
    return wait_for_exported_html(
        downloads_dir,
        timeout=int(os.environ.get("CLI_DOWNLOAD_TIMEOUT", "120")),
        interval=float(os.environ.get("CLI_DOWNLOAD_INTERVAL", "1")),
        since_epoch=time.time(),
    )


def _bookmarks_env() -> dict[str, str]:
    env = os.environ.copy()
    env["CLI_ROOT"] = str(project_root())
    env["CLI_BOOKMARKS_FILE"] = str(bookmarks_file_path())
    env["CLI_DOWNLOADS_DIR"] = str(chrome_downloads_dir())
    return env


def bookmarks_ingest_from_chrome(*, profile: str | None = None) -> None:
    """Exported HTML → local: ingest bookmarks HTML into configured path."""
    dest = bookmarks_file_path(profile)
    fixture = os.environ.get("CLI_BOOKMARKS_FIXTURE") or os.environ.get("CLI_BOOKMARKS_SOURCE")
    source_path = _resolve_source_path(fixture)
    since = None if os.environ.get("CLI_SKIP_CHROME_AUTOMATION") == "1" else time.time()
    try:
        export_bookmarks(
            dest,
            downloads_dir=chrome_downloads_dir(),
            source=source_path,
            timeout=int(os.environ.get("CLI_DOWNLOAD_TIMEOUT", "120")),
            interval=float(os.environ.get("CLI_DOWNLOAD_INTERVAL", "1")),
            since_epoch=since,
        )
    except (FileNotFoundError, TimeoutError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    rprint(f"[green]ingested[/green] → {dest}")


def bookmarks_deploy_to_chrome(*, profile: str | None = None) -> None:
    """Local backup → terminal: validate backup file for browser import."""
    src = bookmarks_file_path(profile)
    try:
        import_bookmarks(src)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"{exc}\nRun `cli chrome bookmarks ingest` first.", err=True)
        raise typer.Exit(1) from exc
    rprint(f"[green]ready[/green] for browser import from {src}")


@bookmarks_app.command("ingest")
def bookmarks_ingest_cmd(
    profile: str | None = typer.Option(None, "--profile", help="Chrome profile key from config."),
) -> None:
    """Exported HTML → local: ingest bookmarks HTML to configured path."""
    bookmarks_ingest_from_chrome(profile=profile)


@bookmarks_app.command("deploy")
def bookmarks_deploy_cmd(
    profile: str | None = typer.Option(None, "--profile", help="Chrome profile key from config."),
) -> None:
    """Local backup → terminal: validate backup for browser import."""
    bookmarks_deploy_to_chrome(profile=profile)


@bookmarks_app.command("merge")
def bookmarks_merge_cmd(
    profile: str | None = typer.Option(None, "--profile", help="Chrome profile key from config."),
    source: str | None = typer.Option(
        None,
        "--source",
        help="HTML export path (default: newest file in chrome.downloads_dir).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report would-add/skip without writing."),
    format: ChromeOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Merge new bookmark URLs from an export into the configured backup (dedupe by URL)."""
    backup = bookmarks_file_path(profile)
    try:
        source_path = _resolve_merge_source(source, downloads_dir=chrome_downloads_dir())
    except (FileNotFoundError, TimeoutError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    try:
        result = merge_bookmarks(backup, source_path, dry_run=dry_run)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if format == ChromeOutputFormat.json:
        _emit_json(
            {
                "dry_run": dry_run,
                "profile": chrome_profile_key(profile),
                "backup": str(backup),
                "source": str(source_path),
                "added": result.added,
                "skipped": result.skipped,
            }
        )
    else:
        label = "Would add" if dry_run else "Added"
        rprint(f"[bold]{label}[/bold] {len(result.added)}  skipped {len(result.skipped)}")
        for url in result.added:
            rprint(f"  [green]+[/green] {url}")
        for url in result.skipped:
            rprint(f"  [dim]skip[/dim] {url}")


@bookmarks_app.command("snapshot")
def bookmarks_snapshot_cmd(
    profile: str | None = typer.Option(None, "--profile", help="Chrome profile key from config."),
    format: ChromeOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Copy the current backup to a timestamped file under chrome.snapshots_dir."""
    backup = bookmarks_file_path(profile)
    snapshots_dir = chrome_snapshots_dir()
    if snapshots_dir is None:
        typer.echo(
            "chrome.snapshots_dir is not configured. Set chrome.snapshots_dir in config/config.yaml.",
            err=True,
        )
        raise typer.Exit(1)
    profile_key = chrome_profile_key(profile)
    try:
        dest = snapshot_bookmarks(
            backup,
            snapshots_dir,
            profile_key,
            retention=chrome_snapshot_retention(),
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if format == ChromeOutputFormat.json:
        _emit_json({"profile": profile_key, "backup": str(backup), "snapshot": str(dest)})
    else:
        rprint(f"[green]snapshot[/green] {dest}")


@bookmarks_app.command("import", hidden=True)
def legacy_import_cmd() -> None:
    """Deprecated: remote-centric local→Chrome; use `cli chrome bookmarks deploy`."""
    bookmarks_deploy_to_chrome()


@bookmarks_app.command("export", hidden=True)
def legacy_export_cmd() -> None:
    """Deprecated: remote-centric Chrome→local; use `cli chrome bookmarks ingest`."""
    bookmarks_ingest_from_chrome()


@photos_app.command("list")
def photos_list_cmd(
    format: ChromeOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """List albums ingested under chrome.photos_dir."""
    try:
        photos_dir = photos_dir_path()
        albums = list_albums(photos_dir)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if format == ChromeOutputFormat.json:
        _emit_json(
            {
                "photos_dir": str(photos_dir),
                "albums": [
                    {
                        "slug": album.slug,
                        "title": album.title,
                        "media_count": album.media_count,
                        "path": album.path,
                    }
                    for album in albums
                ],
            }
        )
        return

    if not albums:
        rprint("[dim]No albums ingested yet.[/dim]")
        return
    for album in albums:
        rprint(f"[bold]{album.title}[/bold] ({album.slug}) — {album.media_count} files")


@photos_app.command("status")
def photos_status_cmd(
    format: ChromeOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Summarize local Google Photos inventory."""
    try:
        payload = photos_status(photos_dir_path())
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if format == ChromeOutputFormat.json:
        _emit_json(payload)
        return

    rprint(f"[bold]photos_dir[/bold] {payload['photos_dir']}")
    rprint(f"albums {payload['album_count']}  media {payload['media_count']}")
    if payload.get("last_ingest"):
        rprint(f"last_ingest {payload['last_ingest']}")


@photos_app.command("ingest")
def photos_ingest_cmd(
    source: str | None = typer.Option(
        None,
        "--source",
        help="Takeout .zip or extracted directory (default: newest .zip in takeout dir).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report planned copies without writing."),
    yes: bool = typer.Option(False, "--yes", help="Skip write gate in non-interactive mode."),
    format: ChromeOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Import Google Takeout album media into chrome.photos_dir."""
    try:
        photos_dir = photos_dir_path()
        takeout_dir = photos_takeout_dir()
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    source_path = _resolve_source_path(
        os.environ.get("CLI_PHOTOS_SOURCE") or os.environ.get("CLI_PHOTOS_FIXTURE") or source
    )
    if not dry_run:
        require_write_gate(
            "chrome-photos-ingest",
            [f"photos_dir: {photos_dir}", f"takeout_dir: {takeout_dir}"],
            question="Import Google Photos Takeout into the configured photos_dir?",
            yes=yes,
        )

    since = None if os.environ.get("CLI_SKIP_CHROME_AUTOMATION") == "1" else time.time()
    try:
        result = ingest_takeout(
            photos_dir,
            takeout_dir,
            source=source_path,
            dry_run=dry_run,
            timeout=int(os.environ.get("CLI_DOWNLOAD_TIMEOUT", "120")),
            interval=float(os.environ.get("CLI_DOWNLOAD_INTERVAL", "1")),
            since_epoch=since,
        )
    except (FileNotFoundError, TimeoutError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if format == ChromeOutputFormat.json:
        _emit_json(
            {
                "dry_run": dry_run,
                "photos_dir": str(photos_dir),
                "source": result.source,
                "albums": result.albums,
                "media_files": result.media_files,
            }
        )
        return

    label = "Would ingest" if dry_run else "Ingested"
    rprint(f"[green]{label}[/green] {result.media_files} files across {len(result.albums)} albums")
    for slug in result.albums:
        rprint(f"  [green]+[/green] {slug}")


chrome_app.add_typer(bookmarks_app, name="bookmarks")
chrome_app.add_typer(photos_app, name="photos")
