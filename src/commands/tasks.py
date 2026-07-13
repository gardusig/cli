"""Task pair shortcuts and ingest workflow."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from rich import print as rprint

from src.commands.notion import pairs_build_cmd
from src.internal.write.gate import require_write_gate
from src.services.notion_pairs import load_pairs, pair_file_warning, scan_task_root
from src.services.notion_sync import export_tasks
from src.utils.config import load_config, notion_pairs_file, notion_task_root, require_notion_token

tasks_app = typer.Typer(help="Task pairs and local ingest shortcuts.", no_args_is_help=True)
pairs_app = typer.Typer(help="Task pair manifest checks.", no_args_is_help=True)
tasks_app.add_typer(pairs_app, name="pairs")


def _emit(data: object, fmt: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, list):
            for row in data:
                typer.echo(str(row))
        else:
            typer.echo(str(data))


@tasks_app.command("list")
def list_cmd() -> None:
    """Show task shortcuts."""
    _emit(
        [
            {"target": "notion", "ops": ["deploy", "ingest"]},
            {"target": "pairs", "ops": ["validate", "build"]},
        ],
        "json",
    )


@tasks_app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_cmd(
    ctx: typer.Context,
    target: str,
    op: str,
) -> None:
    """Short dispatcher for task-related commands."""
    from src.commands.notion import deploy_cmd as notion_deploy_cmd
    from src.commands.notion import ingest_cmd as notion_ingest_cmd

    args = list(ctx.args)
    if target == "notion" and op == "deploy":
        notion_deploy_cmd(yes="--yes" in args or "-y" in args, cleanup=None)
    elif target == "notion" and op == "ingest":
        notion_ingest_cmd()
    else:
        raise typer.Exit(f"Unknown task operation: {target} {op}")


@pairs_app.command("validate")
def pairs_validate_cmd(format: str = typer.Option("table", "--format")) -> None:
    """Validate tasks.pairs.json against header/body files."""
    root = notion_task_root()
    manifest = notion_pairs_file()
    pairs = load_pairs(manifest, task_root=root)
    scan = scan_task_root(root)
    rows = []
    errors: list[str] = []
    seen = set()
    for pair in pairs:
        warning = pair_file_warning(pair, root)
        status = "ok" if warning is None else "missing"
        rows.append(
            {
                "header": pair.header_filepath,
                "body": pair.body_filepath,
                "status": status,
                "warning": warning or "",
            }
        )
        if warning:
            errors.append(warning)
        seen.add((pair.header_filepath, pair.body_filepath))
    for warning in scan.warnings:
        errors.append(warning)
    _emit(rows, format)
    if errors:
        raise typer.Exit(1)


@pairs_app.command("build")
def pairs_build_task_cmd() -> None:
    """Rebuild tasks.pairs.json from configured task root."""
    pairs_build_cmd()


@tasks_app.command("ingest-pr", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def ingest_pr_cmd(
    source: str = typer.Option(..., "--source"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Ingest from Notion, rebuild pairs, commit, and push a branch."""
    root = notion_task_root()
    require_write_gate(
        f"tasks-ingest-pr-{source}",
        [f"task_root: {root}", "scope: tasks/ only"],
        question=f"Ingest from {source} and push a task-data branch?",
        yes=yes,
    )
    if source != "notion":
        raise typer.Exit("source must be notion")
    cfg = load_config()
    export_tasks(root, token=require_notion_token(cfg), config=cfg.notion)
    pairs_build_cmd()
    pairs_validate_cmd(format="json")

    diff = subprocess.run(["git", "status", "--short", "tasks"], text=True, capture_output=True, check=True).stdout
    if not diff.strip():
        rprint("[green]no changes[/green]")
        return
    branch = f"sync/{source}-{datetime.now().strftime('%Y%m%d')}"
    subprocess.run(["git", "switch", "-c", branch], check=True)
    subprocess.run(["git", "add", "tasks"], check=True)
    subprocess.run(["git", "commit", "-m", f"Sync tasks from {source}"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], check=True)
