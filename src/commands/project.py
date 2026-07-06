"""GitHub Projects v2 commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from src.internal.write.gate import require_write_gate
from src.services.project_service import ProjectRef, ProjectService
from src.utils.config import project_pairs_file, project_task_root

project_app = typer.Typer(
    help="GitHub Projects v2 board workflows.",
    no_args_is_help=True,
)
field_app = typer.Typer(help="Project field reads.", no_args_is_help=True)
item_app = typer.Typer(help="Project item reads and writes.", no_args_is_help=True)
pairs_app = typer.Typer(help="Manage project task pairs.", no_args_is_help=True)
recurrence_app = typer.Typer(help="Advance recurrent maintenance issues.", no_args_is_help=True)

project_app.add_typer(field_app, name="field")
project_app.add_typer(item_app, name="item")
project_app.add_typer(pairs_app, name="pairs")
project_app.add_typer(recurrence_app, name="recurrence")


def _svc(repo: str | None = None) -> ProjectService:
    return ProjectService(repo=repo)


def _emit(data: object, fmt: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(data, indent=2))
        return
    if isinstance(data, dict):
        for key, value in data.items():
            typer.echo(f"{key}: {value}")
        return
    if isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                label = row.get("title") or row.get("name") or row.get("id") or row
                typer.echo(str(label))
            else:
                typer.echo(str(row))
        return
    typer.echo(str(data))


def _ctx_format(ctx: typer.Context) -> str:
    return (ctx.obj or {}).get("format") or "json"


def _ctx_repo(ctx: typer.Context) -> str | None:
    return (ctx.obj or {}).get("repo")


def _ref(
    svc: ProjectService,
    *,
    owner: str | None = None,
    number: int | None = None,
    project_id: str | None = None,
) -> ProjectRef:
    return svc.ref(owner=owner, number=number, project_id=project_id)


def _gate(
    operation: str,
    svc: ProjectService,
    ref: ProjectRef,
    *,
    yes: bool,
    question: str,
    extra_lines: list[str] | None = None,
) -> None:
    require_write_gate(
        operation,
        svc.snapshot_summary(ref),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )


@project_app.callback()
def project_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="owner/name for issue and PR lookups."),
    format: str = typer.Option("json", "--format", help="json or table"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
    ctx.obj["format"] = format


@project_app.command("list")
def project_list_cmd(
    ctx: typer.Context,
    owner: str = typer.Option("gardusig", "--owner"),
    limit: int = typer.Option(30, "--limit"),
) -> None:
    _emit(_svc(_ctx_repo(ctx)).project_list(owner=owner, limit=limit), _ctx_format(ctx))


@project_app.command("view")
def project_view_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    _emit(svc.project_view(ref.require_number(), owner=ref.owner), _ctx_format(ctx))


@field_app.command("list")
def field_list_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.field_list(_ref(svc, owner=owner, number=number)), _ctx_format(ctx))


@item_app.command("list")
def item_list_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
    limit: int = typer.Option(100, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.item_list(_ref(svc, owner=owner, number=number), limit=limit), _ctx_format(ctx))


@item_app.command("view")
def item_view_cmd(
    ctx: typer.Context,
    id: str = typer.Option(..., "--id"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    _emit(svc.item_view(id, _ref(svc, owner=owner, number=number)), _ctx_format(ctx))


@item_app.command("add")
def item_add_cmd(
    ctx: typer.Context,
    url: str | None = typer.Option(None, "--url"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    lane: str | None = typer.Option(None, "--lane"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    if url:
        target = url
    elif issue is not None:
        target = f"issue #{issue}"
    elif pr is not None:
        target = f"pr #{pr}"
    else:
        target = "item"
    _gate("project-item-add", svc, ref, yes=yes, question=f"Add {target} to project?")
    if url:
        data = svc.item_add_url(url, ref)
    elif issue is not None:
        data = svc.item_add_issue(issue, ref)
    elif pr is not None:
        data = svc.item_add_pr(pr, ref)
    else:
        raise typer.Exit("Provide --url, --issue, or --pr.")
    item_id = str(data.get("id") or data.get("item", {}).get("id") or data.get("item_id") or "")
    if lane and item_id:
        svc.item_status(ref, item_id=item_id, status=lane)
        data["lane"] = lane
    _emit(data, _ctx_format(ctx))


@item_app.command("status")
def item_status_cmd(
    ctx: typer.Context,
    status: str = typer.Argument(...),
    id: str | None = typer.Option(None, "--id"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    _gate("project-item-status", svc, ref, yes=yes, question=f"Move project item to {status}?")
    _emit(svc.item_status(ref, item_id=item_id, status=status), _ctx_format(ctx))


@item_app.command("set")
def item_set_cmd(
    ctx: typer.Context,
    field: str = typer.Option(..., "--field"),
    value: str = typer.Option(..., "--value"),
    id: str | None = typer.Option(None, "--id"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    value_kind: str = typer.Option("text", "--kind", help="text, date, or single-select"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    _gate("project-item-set", svc, ref, yes=yes, question=f"Set {field} on project item?")
    _emit(
        svc.item_set(ref, item_id=item_id, field=field, value=value, value_kind=value_kind),
        _ctx_format(ctx),
    )


@item_app.command("archive")
def item_archive_cmd(
    ctx: typer.Context,
    id: str | None = typer.Option(None, "--id"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    _gate("project-item-archive", svc, ref, yes=yes, question="Archive project item?")
    _emit(svc.item_archive(ref, item_id=item_id), _ctx_format(ctx))


@item_app.command("remove")
def item_remove_cmd(
    ctx: typer.Context,
    id: str | None = typer.Option(None, "--id"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    delete: bool = typer.Option(False, "--delete", help="Delete instead of archive."),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = _ref(svc, owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    _gate("project-item-remove", svc, ref, yes=yes, question="Remove project item?")
    data = svc.item_delete(ref, item_id=item_id) if delete else svc.item_archive(ref, item_id=item_id)
    _emit(data, _ctx_format(ctx))


@project_app.command("link")
def project_link_cmd(
    ctx: typer.Context,
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    lane: str | None = typer.Option(None, "--lane"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    item_add_cmd(ctx, issue=issue, pr=pr, url=None, lane=lane, number=None, owner=None, yes=yes)


@project_app.command("unlink")
def project_unlink_cmd(
    ctx: typer.Context,
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    delete: bool = typer.Option(False, "--delete"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    item_remove_cmd(ctx, id=None, issue=issue, pr=pr, delete=delete, number=None, owner=None, yes=yes)


@project_app.command("lane")
def project_lane_cmd(
    ctx: typer.Context,
    lane: str = typer.Argument(...),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    item_status_cmd(ctx, status=lane, id=None, issue=issue, pr=pr, number=None, owner=None, yes=yes)


@project_app.command("spawn")
def spawn_cmd(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    if not dry_run:
        _gate(
            "project-spawn",
            svc,
            svc.default_ref(),
            yes=yes,
            question=f"Create issues and add them to project from {file}?",
        )
    _emit(svc.spawn(file, dry_run=dry_run), _ctx_format(ctx))


@pairs_app.command("build")
def pairs_build_cmd(ctx: typer.Context) -> None:
    _emit(_svc(_ctx_repo(ctx)).build_pairs_manifest(), _ctx_format(ctx))


@pairs_app.command("status")
def pairs_status_cmd(ctx: typer.Context) -> None:
    _emit(_svc(_ctx_repo(ctx)).pairs_status().as_dict(), _ctx_format(ctx))


def _print_project_failures(result: dict[str, Any]) -> None:
    for entry in result.get("failed") or []:
        if isinstance(entry, dict):
            name = entry.get("name") or "?"
            err = entry.get("error") or "unknown error"
        else:
            name, err = entry[0], entry[1]
        typer.echo(f"failed {name}: {err}", err=True)


@project_app.command("deploy")
def deploy_cmd(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = svc.default_ref()
    _gate(
        "project-deploy",
        svc,
        ref,
        yes=yes,
        question="Deploy local project pairs to GitHub Project?",
        extra_lines=[f"task_root: {project_task_root()}", f"manifest: {project_pairs_file()}"],
    )
    result = svc.deploy_pairs(ref=ref)
    _emit(result, _ctx_format(ctx))
    if result.get("failed"):
        _print_project_failures(result)
        raise typer.Exit(1)


@project_app.command("ingest")
def ingest_cmd(ctx: typer.Context) -> None:
    _emit(_svc(_ctx_repo(ctx)).ingest_pairs(), _ctx_format(ctx))


@project_app.command("sync")
def sync_cmd(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = svc.default_ref()
    _gate(
        "project-sync",
        svc,
        ref,
        yes=yes,
        question="Ingest board state and deploy local project pairs?",
    )
    result = svc.sync_pairs(ref=ref)
    _emit(result, _ctx_format(ctx))
    deploy = result.get("deploy") if isinstance(result, dict) else {}
    if isinstance(deploy, dict) and deploy.get("failed"):
        _print_project_failures(deploy)
        raise typer.Exit(1)


@recurrence_app.command("check")
def recurrence_check_cmd(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Alias for recurrence advance (explicit polling workflow)."""
    recurrence_advance_cmd(ctx, yes=yes)


@recurrence_app.command("advance")
def recurrence_advance_cmd(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _svc(_ctx_repo(ctx))
    ref = svc.default_ref()
    _gate(
        "project-recurrence-advance",
        svc,
        ref,
        yes=yes,
        question="Advance closed recurrent maintenance issues?",
    )
    _emit(svc.recurrence_advance(ref=ref), _ctx_format(ctx))
