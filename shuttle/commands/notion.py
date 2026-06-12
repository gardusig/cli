"""Notion task board — ingest / deploy / sync (local markdown source of truth)."""

from __future__ import annotations

import typer
from rich import print as rprint

from shuttle.internal.write.gate import require_write_gate
from shuttle.services.notion_sync import cleanup_board, export_tasks, import_tasks
from shuttle.utils.config import load_config, notion_cleanup_before_deploy, notion_tasks_dir, require_notion_token

notion_app = typer.Typer(
    help="Notion task board sync (local data/tasks markdown).",
    no_args_is_help=True,
)


def _cfg():
    return load_config()


def _token(cfg=None) -> str:
    try:
        return require_notion_token(cfg or _cfg())
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc


@notion_app.command("ingest")
def ingest_cmd() -> None:
    """Notion → local: ingest database pages into task_directory."""
    cfg = _cfg()
    token = _token(cfg)
    task_dir = notion_tasks_dir()
    task_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = export_tasks(task_dir, token=token, config=cfg.notion)
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]ingested[/green] {result.processed} task(s) → {task_dir}")


@notion_app.command("deploy")
def deploy_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    cleanup: bool | None = typer.Option(
        None,
        "--cleanup/--no-cleanup",
        help="Archive existing board pages before deploy (default: notion.cleanup_before_deploy).",
    ),
) -> None:
    """Local → Notion: deploy markdown tasks from task_directory."""
    cfg = _cfg()
    token = _token(cfg)
    task_dir = notion_tasks_dir()
    if not task_dir.is_dir():
        raise typer.Exit(f"Task directory not found: {task_dir}")
    do_cleanup = notion_cleanup_before_deploy(cfg.notion) if cleanup is None else cleanup
    if do_cleanup:
        require_write_gate(
            "notion-deploy-cleanup",
            summary_lines=[f"task_dir: {task_dir}", f"database: {cfg.notion.database_id}"],
            question="Archive all existing Notion pages before deploy?",
            yes=yes,
        )
    try:
        result = import_tasks(
            task_dir,
            token=token,
            config=cfg.notion,
            cleanup_first=do_cleanup,
        )
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]deployed[/green] {result.processed} task(s) from {task_dir}")


@notion_app.command("sync")
def sync_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    cleanup: bool | None = typer.Option(
        None,
        "--cleanup/--no-cleanup",
        help="Archive existing board pages before deploy phase.",
    ),
) -> None:
    """Ingest from Notion, then deploy local tasks back to the board."""
    rprint("[bold]Phase 1 — ingest[/bold] (Notion → task_directory)")
    ingest_cmd()
    rprint()
    rprint("[bold]Phase 2 — deploy[/bold] (task_directory → Notion)")
    deploy_cmd(yes=yes, cleanup=cleanup)


@notion_app.command("cleanup")
def cleanup_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Archive every page in the configured Notion database."""
    cfg = _cfg()
    token = _token(cfg)
    require_write_gate(
        "notion-cleanup",
        summary_lines=[f"database: {cfg.notion.database_id}"],
        question="Archive all pages in the Notion database?",
        yes=yes,
    )
    try:
        result = cleanup_board(token=token, config=cfg.notion)
    except NotImplementedError as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]archived[/green] {result.processed} page(s)")


@notion_app.command("download", hidden=True)
def legacy_download_cmd() -> None:
    """Deprecated: use `shuttle notion ingest`."""
    ingest_cmd()


@notion_app.command("upload", hidden=True)
def legacy_upload_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    cleanup: bool | None = typer.Option(None, "--cleanup/--no-cleanup"),
) -> None:
    """Deprecated: use `shuttle notion deploy`."""
    deploy_cmd(yes=yes, cleanup=cleanup)


@notion_app.command("export", hidden=True)
def legacy_export_cmd() -> None:
    """Deprecated: use `shuttle notion ingest`."""
    ingest_cmd()


@notion_app.command("import", hidden=True)
def legacy_import_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    cleanup: bool | None = typer.Option(None, "--cleanup/--no-cleanup"),
) -> None:
    """Deprecated: use `shuttle notion deploy`."""
    deploy_cmd(yes=yes, cleanup=cleanup)
