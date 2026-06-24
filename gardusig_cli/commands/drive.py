"""Local git-tags store (iCloud) and cloud upload."""

from __future__ import annotations

import typer
from rich import print as rprint

from gardusig_cli.internal.read.git import git_worktree_snapshot
from gardusig_cli.internal.write.gate import require_write_gate
from gardusig_cli.services.backup_repository import (
    SyncResult,
    backup_status,
    delete_repo_tag,
    format_status_lines,
    ingest_repositories,
    list_downloaded_tags,
    resolve_repo_path,
)
from gardusig_cli.services.replica_deploy import deploy_replicas
from gardusig_cli.services.drive_sync import UploadResult
from gardusig_cli.services.git_shortcuts import GitShortcuts
from gardusig_cli.utils.config import tags_dir_path
from gardusig_cli.utils.external_client import ExternalCallError

drive_app = typer.Typer(
    help="Local git-tags (iCloud), replicas (cloud + USB), and deploy.",
    no_args_is_help=True,
)


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
    replica: str | None = typer.Argument(
        None,
        help="Replica name, provider, or USB path label (default: all replicas).",
    ),
) -> None:
    """Ingest all configured repositories, then deploy to replicas (cloud + USB)."""
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    rprint("[bold]Phase 1 — ingest[/bold] (all backup.repositories)")
    try:
        ingest_rows = ingest_repositories()
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    created, replaced, failed = _print_ingest_rows(ingest_rows)
    rprint(
        f"Ingest done. Created: {created}  Replaced: {replaced}  Failed: {failed}"
    )
    rprint()
    rprint("[bold]Phase 2 — deploy[/bold] (replicas: cloud + USB)")
    try:
        deploy_rows = deploy_replicas(local_root, selected=replica)
        up, skip, fail = _print_upload_rows(deploy_rows)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    except ExternalCallError as exc:
        raise typer.Exit(exc.user_message) from exc
    rprint(f"Sync done. Deployed: {up}  Skipped: {skip}  Failed: {fail}")


@drive_app.command("deploy")
def deploy_cmd(
    replica: str | None = typer.Argument(
        None,
        help="Replica name or provider (default: all configured replicas).",
    ),
) -> None:
    """Deploy local tag zips to replicas (cloud drives and/or USB paths)."""
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    try:
        rows = deploy_replicas(local_root, selected=replica)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    except ExternalCallError as exc:
        raise typer.Exit(exc.user_message) from exc
    total_up, total_skip, total_fail = _print_upload_rows(rows)
    rprint(
        f"Done. Deployed: {total_up}  Skipped: {total_skip}  Failed: {total_fail}"
    )


@drive_app.command("upload")
def upload_cmd(
    provider: str | None = typer.Argument(
        None,
        help="google, onedrive, or proton (default: all enabled cloud replicas).",
    ),
) -> None:
    """Deploy missing local zips to cloud replica(s) (append-only)."""
    local_root = tags_dir_path()
    if not local_root.is_dir():
        raise typer.Exit(
            f"Local git-tags folder not found: {local_root}\n"
            "Set backup.tags_dir in config/config.yaml (default: iCloud git-tags)."
        )
    try:
        rows = deploy_replicas(local_root, selected=provider, kinds=("cloud",))
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    except ExternalCallError as exc:
        raise typer.Exit(exc.user_message) from exc
    total_up, total_skip, total_fail = _print_upload_rows(rows)
    rprint(
        f"Done. Uploaded: {total_up}  Skipped: {total_skip}  Failed: {total_fail}"
    )
