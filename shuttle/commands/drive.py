"""Local git-tags store (iCloud) and cloud upload."""

from __future__ import annotations

import typer
from rich import print as rprint

from shuttle.internal.read.git import git_worktree_snapshot
from shuttle.internal.write.gate import require_write_gate
from shuttle.providers import google_drive, onedrive, proton_drive
from shuttle.providers.base import DriveProvider
from shuttle.services.backup_repository import (
    SyncResult,
    backup_status,
    delete_repo_tag,
    format_status_lines,
    ingest_repositories,
    list_downloaded_tags,
    resolve_repo_path,
)
from shuttle.services.drive_sync import UploadResult, sync_all, upload_missing
from shuttle.services.git_shortcuts import GitShortcuts
from shuttle.utils.config import load_config, tags_dir_path

drive_app = typer.Typer(
    help="Local git-tags (iCloud) and cloud upload.",
    no_args_is_help=True,
)


def _enabled_providers(selected: str | None) -> list[tuple[str, DriveProvider, str]]:
    cfg = load_config()
    mapping = {
        "google": (cfg.drives.google, google_drive),
        "onedrive": (cfg.drives.onedrive, onedrive),
        "proton": (cfg.drives.proton, proton_drive),
    }
    if selected:
        if selected not in mapping:
            raise typer.BadParameter(f"Unknown provider: {selected}")
        pcfg, module = mapping[selected]
        if not pcfg.enabled:
            raise typer.Exit(f"Provider {selected} is disabled in drives.yaml")
        if not pcfg.root:
            raise typer.Exit(f"Provider {selected} has no root configured")
        return [(selected, module, pcfg.root)]
    rows: list[tuple[str, DriveProvider, str]] = []
    for name, (pcfg, module) in mapping.items():
        if pcfg.enabled and pcfg.root:
            rows.append((name, module, pcfg.root))
    if not rows:
        raise typer.Exit("No enabled drive providers with root configured.")
    return rows


def _print_ingest_rows(rows: list[tuple[Path, SyncResult]]) -> tuple[int, int, int]:
    total_created = total_replaced = total_failed = 0
    for repo, result in rows:
        rprint(f"[bold]Repository[/bold] {repo.name} ({repo})")
        for tag in result.created:
            rprint(f"  [green]✓[/green] {tag}")
        for tag in result.replaced:
            rprint(f"  [green]↻[/green] {tag} (replaced)")
        for tag, err in result.failed:
            label = tag or "(repo)"
            rprint(f"  [red]✗[/red] {label}: {err}")
        total_created += len(result.created)
        total_replaced += len(result.replaced)
        total_failed += len(result.failed)
    return total_created, total_replaced, total_failed


def _print_upload_rows(uploads: list[tuple[str, UploadResult]]) -> tuple[int, int, int]:
    total_up = total_skip = total_fail = 0
    for name, upload in uploads:
        rprint(f"[bold]Uploading to {name}[/bold]")
        for rel in upload.uploaded:
            rprint(f"  [green]✓[/green] {rel}")
        for rel in upload.skipped:
            rprint(f"  [dim]skip[/dim] {rel}")
        for rel, err in upload.failed:
            rprint(f"  [red]✗[/red] {rel}: {err}")
        total_up += len(upload.uploaded)
        total_skip += len(upload.skipped)
        total_fail += len(upload.failed)
    return total_up, total_skip, total_fail


@drive_app.command("status")
def status_cmd() -> None:
    """Show git tags vs local zips for configured repositories."""
    for line in format_status_lines(backup_status()):
        rprint(line.rstrip())


@drive_app.command("ingest")
def ingest_cmd(
    path: str | None = typer.Argument(
        None,
        help="Repository path (default: every entry in backup.repositories).",
    ),
) -> None:
    """Zip every local git tag into git-tags/REPO/ (create or replace)."""
    try:
        rows = ingest_repositories(path)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    total_created, total_replaced, total_failed = _print_ingest_rows(rows)
    rprint(
        f"Done. Created: {total_created}  "
        f"Replaced: {total_replaced}  Failed: {total_failed}"
    )


@drive_app.command("list")
def list_cmd(
    path: str | None = typer.Argument(None, help="Repository path (default: cwd)."),
) -> None:
    """List tag zips stored under git-tags/REPO/."""
    try:
        repo = resolve_repo_path(path)
        tags = list_downloaded_tags(repo)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[bold]Local zips[/bold] {repo.name} ({len(tags)}):")
    for tag in tags:
        rprint(f"  {tag}")
    if not tags:
        rprint("  (none)")


@drive_app.command("delete")
def delete_cmd(
    path: str = typer.Argument(..., help="Repository path."),
    tag: str = typer.Argument(..., help="Tag name (zip stem)."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Delete git-tags/REPO/TAG.zip from local store."""
    try:
        repo = resolve_repo_path(path)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    snapshot = git_worktree_snapshot(GitShortcuts(top=str(repo)))
    require_write_gate(
        "drive-delete",
        snapshot.summary_lines(),
        question=f"Delete local zip for tag {tag}?",
        yes=yes,
        extra_lines=[f"repo: {repo}", f"tag: {tag}"],
    )
    try:
        deleted = delete_repo_tag(str(repo), tag)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]deleted[/green] {deleted.name}")


@drive_app.command("sync")
def sync_cmd(
    provider: str | None = typer.Argument(
        None,
        help="google, onedrive, or proton (default: all enabled).",
    ),
) -> None:
    """Ingest all configured repositories, then upload to all enabled cloud providers."""
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    try:
        targets = _enabled_providers(provider)
    except typer.BadParameter:
        raise
    rprint("[bold]Phase 1 — ingest[/bold] (all backup.repositories)")
    try:
        sync_result = sync_all(local_root, targets)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    created, replaced, failed = _print_ingest_rows(sync_result.ingest)
    rprint(
        f"Ingest done. Created: {created}  Replaced: {replaced}  Failed: {failed}"
    )
    rprint()
    rprint("[bold]Phase 2 — upload[/bold] (append-only)")
    try:
        up, skip, fail = _print_upload_rows(sync_result.uploads)
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"Sync done. Uploaded: {up}  Skipped: {skip}  Failed: {fail}")


@drive_app.command("upload")
def upload_cmd(
    provider: str | None = typer.Argument(
        None,
        help="google, onedrive, or proton (default: all enabled).",
    ),
) -> None:
    """Upload missing local zips to cloud drive(s) (append-only)."""
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    try:
        targets = _enabled_providers(provider)
    except typer.BadParameter:
        raise
    uploads: list[tuple[str, UploadResult]] = []
    for name, module, remote_root in targets:
        rprint(f"[bold]Uploading to {name}[/bold] (root: {remote_root})")
        try:
            uploads.append((name, upload_missing(local_root, module, remote_root)))
        except NotImplementedError as exc:
            raise typer.Exit(str(exc)) from exc
    total_up, total_skip, total_fail = _print_upload_rows(uploads)
    rprint(
        f"Done. Uploaded: {total_up}  Skipped: {total_skip}  Failed: {total_fail}"
    )
