"""Notion task board — ingest / deploy / sync (local markdown source of truth)."""

from __future__ import annotations

import typer
from rich import print as rprint

from shuttle.internal.write.gate import require_write_gate
from shuttle.services.notion_sync import (
    build_pairs_manifest,
    cleanup_board,
    export_tasks,
    import_tasks,
)
from shuttle.utils.config import (
    load_config,
    notion_cleanup_before_deploy,
    notion_pairs_file,
    notion_task_root,
    require_notion_token,
)

notion_app = typer.Typer(
    help="Notion task board sync (header/body pairs + tasks.pairs.json).",
    no_args_is_help=True,
)

pairs_app = typer.Typer(help="Manage tasks.pairs.json manifest.")
notion_app.add_typer(pairs_app, name="pairs")


def _cfg():
    return load_config()


def _token(cfg=None) -> str:
    try:
        return require_notion_token(cfg or _cfg())
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc


def _print_sync_warnings(result) -> None:
    for warning in getattr(result, "warnings", []):
        rprint(f"[yellow]warning[/yellow] {warning}")


@notion_app.command("ingest")
def ingest_cmd() -> None:
    """Notion → local: ingest database pages into task pairs."""
    cfg = _cfg()
    token = _token(cfg)
    root = notion_task_root()
    root.mkdir(parents=True, exist_ok=True)
    try:
        result = export_tasks(root, token=token, config=cfg.notion)
    except Exception as exc:
        raise typer.Exit(str(exc)) from exc
    _print_sync_warnings(result)
    rprint(
        f"[green]ingested[/green] {result.processed} task(s) → {root} "
        f"({notion_pairs_file().name})"
    )


@notion_app.command("deploy")
def deploy_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    cleanup: bool | None = typer.Option(
        None,
        "--cleanup/--no-cleanup",
        help="Archive existing board pages before deploy (default: notion.cleanup_before_deploy).",
    ),
) -> None:
    """Local → Notion: deploy task pairs from tasks.pairs.json."""
    cfg = _cfg()
    token = _token(cfg)
    root = notion_task_root()
    manifest = notion_pairs_file()
    if not manifest.is_file():
        raise typer.Exit(f"Pairs manifest not found: {manifest}. Run: shuttle notion pairs build")
    do_cleanup = notion_cleanup_before_deploy(cfg.notion) if cleanup is None else cleanup
    if do_cleanup:
        require_write_gate(
            "notion-deploy-cleanup",
            summary_lines=[f"task_root: {root}", f"database: {cfg.notion.database_id}"],
            question="Archive all existing Notion pages before deploy?",
            yes=yes,
        )
    try:
        result = import_tasks(
            root,
            token=token,
            config=cfg.notion,
            cleanup_first=do_cleanup,
        )
    except Exception as exc:
        raise typer.Exit(str(exc)) from exc
    _print_sync_warnings(result)
    rprint(
        f"[green]deployed[/green] {result.processed} task(s) from {manifest} "
        f"(skipped {result.skipped})"
    )


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
    rprint("[bold]Phase 1 — ingest[/bold] (Notion → task_root)")
    ingest_cmd()
    rprint()
    rprint("[bold]Phase 2 — deploy[/bold] (task_root → Notion)")
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
    except Exception as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]archived[/green] {result.processed} page(s)")


@pairs_app.command("build")
def pairs_build_cmd() -> None:
    """Scan header/ + body/ and write tasks.pairs.json (name must be in each yaml)."""
    root = notion_task_root()
    try:
        result = build_pairs_manifest(root)
    except Exception as exc:
        raise typer.Exit(str(exc)) from exc
    rprint(f"[green]built[/green] {result.processed} pair(s) → {notion_pairs_file()}")


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
