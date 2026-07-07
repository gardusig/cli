"""Local git-tags store (iCloud) and cloud upload."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint

from src.internal.read.git import git_worktree_snapshot
from src.internal.write.gate import require_write_gate
from src.services.backup_repository import (
    SyncResult,
    backup_status,
    delete_repo_tag,
    format_status_lines,
    ingest_repositories,
    list_downloaded_tags,
    plan_ingest_repositories,
    resolve_repo_path,
)
from src.services.drive_sync import DownloadResult, UploadResult
from src.services.git_shortcuts import GitShortcuts
from src.services.replica_deploy import (
    deploy_replicas,
    download_replicas,
    preflight_replicas,
)
from src.utils.config import tags_dir_path

drive_app = typer.Typer(
    help="Local git-tags (iCloud), replicas (cloud + USB), and deploy.",
    no_args_is_help=True,
)


class DriveOutputFormat(str, Enum):
    table = "table"
    json = "json"


def _emit_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2))


def _upload_payload(rows: list[tuple[str, UploadResult]], *, dry_run: bool) -> dict[str, Any]:
    return {
        "dry_run": dry_run,
        "replicas": [
            {
                "name": name,
                "uploaded": upload.uploaded,
                "skipped": upload.skipped,
                "failed": [{"path": path, "error": err} for path, err in upload.failed],
            }
            for name, upload in rows
        ],
    }


def _download_payload(rows: list[tuple[str, DownloadResult]], *, dry_run: bool) -> dict[str, Any]:
    return {
        "dry_run": dry_run,
        "replicas": [
            {
                "name": name,
                "downloaded": row.downloaded,
                "skipped": row.skipped,
                "failed": [{"path": path, "error": err} for path, err in row.failed],
            }
            for name, row in rows
        ],
    }


def _exit_if_failures(*counts: int, strict: bool = True) -> None:
    if strict and any(count > 0 for count in counts):
        raise typer.Exit(1)


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


def _upload_action_label(dry_run: bool) -> str:
    return "Would upload" if dry_run else "Uploading"


def _print_upload_rows(
    uploads: list[tuple[str, UploadResult]],
    *,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    total_up = total_skip = total_fail = 0
    action = "would upload" if dry_run else "uploaded"
    for name, upload in uploads:
        rprint(f"[bold]{_upload_action_label(dry_run)} to {name}[/bold]")
        for rel in upload.uploaded:
            rprint(f"  [green]✓[/green] {rel}")
        for rel in upload.skipped:
            rprint(f"  [dim]skip[/dim] {rel}")
        for rel, err in upload.failed:
            label = rel or "(replica)"
            rprint(f"  [red]✗[/red] {label}: {err}")
        total_up += len(upload.uploaded)
        total_skip += len(upload.skipped)
        total_fail += len(upload.failed)
    if dry_run and total_up:
        rprint(f"[dim]dry-run: {total_up} file(s) {action}[/dim]")
    return total_up, total_skip, total_fail


def _print_download_rows(
    rows: list[tuple[str, DownloadResult]],
    *,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    total_down = total_skip = total_fail = 0
    for name, row in rows:
        label = "Would download from" if dry_run else "Downloading from"
        rprint(f"[bold]{label} {name}[/bold]")
        for rel in row.downloaded:
            rprint(f"  [green]✓[/green] {rel}")
        for rel in row.skipped:
            rprint(f"  [dim]skip[/dim] {rel}")
        for rel, err in row.failed:
            label_path = rel or "(replica)"
            rprint(f"  [red]✗[/red] {label_path}: {err}")
        total_down += len(row.downloaded)
        total_skip += len(row.skipped)
        total_fail += len(row.failed)
    return total_down, total_skip, total_fail


@drive_app.command("status")
def status_cmd(
    replicas: bool = typer.Option(
        False,
        "--replicas",
        help="Include read-only cloud/USB replica gap summary.",
    ),
    format: DriveOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Show git tags vs local zips for configured repositories."""
    lines = [line.rstrip() for line in format_status_lines(backup_status())]
    replica_rows = []
    if replicas:
        local_root = tags_dir_path()
        try:
            replica_rows = preflight_replicas(local_root)
        except RuntimeError as exc:
            raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json:
        payload: dict[str, Any] = {"repositories": lines}
        if replicas:
            payload["replicas"] = [
                {
                    "name": row.name,
                    "local_count": row.local_count,
                    "remote_count": row.remote_count,
                    "missing_remote": row.missing_remote,
                    "failed": [{"path": p, "error": e} for p, e in row.failed],
                }
                for row in replica_rows
            ]
        _emit_json(payload)
        return

    for line in lines:
        rprint(line)
    if replicas:
        rprint()
        rprint("[bold]Replica preflight[/bold]")
        for row in replica_rows:
            if row.failed:
                for _, err in row.failed:
                    rprint(f"  [red]✗[/red] {row.name}: {err}")
                continue
            rprint(
                f"  {row.name}: local={row.local_count} remote={row.remote_count} "
                f"missing_remote={len(row.missing_remote)}"
            )


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
    _exit_if_failures(total_failed)


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


def _require_tags_dir() -> Path:
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    return local_root


def _ingest_payload(rows: list[tuple[Path, SyncResult]]) -> list[dict[str, Any]]:
    return [
        {
            "repo": str(repo),
            "created": result.created,
            "replaced": result.replaced,
            "failed": [{"tag": tag, "error": err} for tag, err in result.failed],
        }
        for repo, result in rows
    ]


def _replica_preflight_payload(rows: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": row.name,
            "local_count": row.local_count,
            "remote_count": row.remote_count,
            "missing_remote": row.missing_remote,
            "failed": [{"path": path, "error": err} for path, err in row.failed],
        }
        for row in rows
    ]


def _emit_sync_status(
    *,
    ingest_rows: list[tuple[Path, SyncResult]],
    replica_rows: list[Any],
    format: DriveOutputFormat,
) -> None:
    if format == DriveOutputFormat.json:
        _emit_json(
            {
                "status": True,
                "ingest": _ingest_payload(ingest_rows),
                "replicas": _replica_preflight_payload(replica_rows),
            }
        )
        return
    rprint("[bold]Ingest plan[/bold] (backup.repositories)")
    created, replaced, failed = _print_ingest_rows(ingest_rows)
    rprint(f"Would create: {created}  Would replace: {replaced}  Failed: {failed}")
    rprint()
    rprint("[bold]Replica preflight[/bold]")
    for row in replica_rows:
        if row.failed:
            for _, err in row.failed:
                rprint(f"  [red]✗[/red] {row.name}: {err}")
            continue
        rprint(
            f"  {row.name}: local={row.local_count} remote={row.remote_count} "
            f"missing_remote={len(row.missing_remote)}"
        )


@drive_app.command("sync")
def sync_cmd(
    replica: str | None = typer.Argument(
        None,
        help="Replica name, provider, or USB path label (default: all replicas).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute actions without writing."),
    status: bool = typer.Option(
        False,
        "--status",
        help="Preflight only: ingest plan + replica gaps (no writes).",
    ),
    strict: bool = typer.Option(
        True,
        "--strict/--no-strict",
        help="Exit 1 when any ingest or deploy leg reports failures (default: strict).",
    ),
    format: DriveOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Ingest all configured repositories, then deploy to replicas (cloud + USB)."""
    local_root = _require_tags_dir()
    if status:
        try:
            ingest_rows = plan_ingest_repositories()
            replica_rows = preflight_replicas(local_root, selected=replica)
        except RuntimeError as exc:
            raise typer.Exit(str(exc)) from exc
        _emit_sync_status(ingest_rows=ingest_rows, replica_rows=replica_rows, format=format)
        ingest_fail = sum(len(r.failed) for _, r in ingest_rows)
        replica_fail = sum(len(r.failed) for r in replica_rows)
        _exit_if_failures(ingest_fail, replica_fail, strict=strict)
        return

    try:
        if dry_run:
            ingest_rows = plan_ingest_repositories()
        else:
            ingest_rows = ingest_repositories()
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json and dry_run:
        deploy_rows = deploy_replicas(local_root, selected=replica, dry_run=True)
        _emit_json(
            {
                "dry_run": True,
                "ingest": _ingest_payload(ingest_rows),
                **_upload_payload(deploy_rows, dry_run=True),
            }
        )
        ingest_fail = sum(len(r.failed) for _, r in ingest_rows)
        deploy_fail = sum(len(r.failed) for _, r in deploy_rows)
        _exit_if_failures(ingest_fail, deploy_fail, strict=strict)
        return

    rprint("[bold]Phase 1 — ingest[/bold] (all backup.repositories)")
    if dry_run:
        created, replaced, failed = _print_ingest_rows(ingest_rows)
        rprint(
            f"Ingest plan. Would create: {created}  Would replace: {replaced}  Failed: {failed}"
        )
    else:
        created, replaced, failed = _print_ingest_rows(ingest_rows)
        rprint(
            f"Ingest done. Created: {created}  Replaced: {replaced}  Failed: {failed}"
        )
    rprint()
    rprint("[bold]Phase 2 — deploy[/bold] (replicas: cloud + USB)")
    try:
        deploy_rows = deploy_replicas(local_root, selected=replica, dry_run=dry_run)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json:
        _emit_json(
            {
                "dry_run": dry_run,
                "ingest": _ingest_payload(ingest_rows),
                **_upload_payload(deploy_rows, dry_run=dry_run),
            }
        )
    else:
        up, skip, fail = _print_upload_rows(deploy_rows, dry_run=dry_run)
        label = "Would deploy" if dry_run else "Deployed"
        rprint(f"Sync done. {label}: {up}  Skipped: {skip}  Failed: {fail}")

    ingest_fail = sum(len(r.failed) for _, r in ingest_rows)
    deploy_fail = sum(len(r.failed) for _, r in deploy_rows)
    _exit_if_failures(ingest_fail, deploy_fail, strict=strict)


@drive_app.command("deploy")
def deploy_cmd(
    replica: str | None = typer.Argument(
        None,
        help="Replica name or provider (default: all configured replicas).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute actions without writing."),
    format: DriveOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Deploy local tag zips to replicas (cloud drives and/or USB paths)."""
    local_root = _require_tags_dir()
    try:
        rows = deploy_replicas(local_root, selected=replica, dry_run=dry_run)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json:
        _emit_json(_upload_payload(rows, dry_run=dry_run))
    else:
        total_up, total_skip, total_fail = _print_upload_rows(rows, dry_run=dry_run)
        label = "Would deploy" if dry_run else "Deployed"
        rprint(
            f"Done. {label}: {total_up}  Skipped: {total_skip}  Failed: {total_fail}"
        )
    total_fail = sum(len(r.failed) for _, r in rows)
    _exit_if_failures(total_fail)


@drive_app.command("upload")
def upload_cmd(
    provider: str | None = typer.Argument(
        None,
        help="google, onedrive, or proton (default: all enabled cloud replicas).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute actions without writing."),
    format: DriveOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Deploy missing local zips to cloud replica(s) (append-only)."""
    local_root = _require_tags_dir()
    try:
        rows = deploy_replicas(
            local_root,
            selected=provider,
            kinds=("cloud",),
            dry_run=dry_run,
        )
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json:
        _emit_json(_upload_payload(rows, dry_run=dry_run))
    else:
        total_up, total_skip, total_fail = _print_upload_rows(rows, dry_run=dry_run)
        label = "Would upload" if dry_run else "Uploaded"
        rprint(
            f"Done. {label}: {total_up}  Skipped: {total_skip}  Failed: {total_fail}"
        )
    total_fail = sum(len(r.failed) for _, r in rows)
    _exit_if_failures(total_fail)


@drive_app.command("download")
def download_cmd(
    provider: str | None = typer.Argument(
        None,
        help="google or onedrive (default: all enabled cloud replicas).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute actions without writing."),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite local files that already exist.",
    ),
    format: DriveOutputFormat = typer.Option("table", "--format", help="table or json"),
) -> None:
    """Download missing remote zips into the local git-tags hub (one-way restore)."""
    local_root = _require_tags_dir()
    try:
        rows = download_replicas(
            local_root,
            selected=provider,
            dry_run=dry_run,
            force=force,
        )
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc

    if format == DriveOutputFormat.json:
        _emit_json(_download_payload(rows, dry_run=dry_run))
    else:
        total_down, total_skip, total_fail = _print_download_rows(rows, dry_run=dry_run)
        label = "Would download" if dry_run else "Downloaded"
        rprint(
            f"Done. {label}: {total_down}  Skipped: {total_skip}  Failed: {total_fail}"
        )
    total_fail = sum(len(r.failed) for _, r in rows)
    _exit_if_failures(total_fail)
