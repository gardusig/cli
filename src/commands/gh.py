"""GitHub (`gh`) subcommands — JSON-first, write gates."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from src.commands.git import _interactive_allow_main
from src.internal.write.gate import require_write_gate
from src.providers.gh_transport import GhTransportMode
from src.services.gh_issues_sync import deploy_issues, ingest_issues, prune_issues
from src.services.gh_policy import (
    blocked_operations_catalog,
    policy_for_cli_command,
)
from src.services.gh_pr_shortcut import GhPrShortcut
from src.services.gh_service import GhService
from src.services.gh_topo import load_priority_levels
from src.services.project_service import ProjectService
from src.commands.gh_wf import wf_app
from src.utils.config import project_auto_link

gh_app = typer.Typer(help="GitHub via gh — issues, labels, PRs, backlog.", no_args_is_help=True)
issue_app = typer.Typer(help="Issue read/write.", no_args_is_help=True)
issues_app = typer.Typer(help="Issue sync/deploy helpers.", no_args_is_help=True)
label_app = typer.Typer(help="Label read/write.", no_args_is_help=True)
pr_app = typer.Typer(help="Pull request read/write.", no_args_is_help=False)
backlog_app = typer.Typer(help="Backlog tree, next, resequence.", no_args_is_help=True)
project_app = typer.Typer(help="GitHub Projects read/write.", no_args_is_help=True)
project_item_app = typer.Typer(help="GitHub Project item read/write.", no_args_is_help=True)
ruleset_app = typer.Typer(
    help="GitHub Rulesets (blocked — use GitHub UI).",
    no_args_is_help=True,
)
policy_app = typer.Typer(help="CLI GitHub policy.", no_args_is_help=True)

gh_app.add_typer(issue_app, name="issue")
gh_app.add_typer(issues_app, name="issues")
gh_app.add_typer(label_app, name="label")
gh_app.add_typer(pr_app, name="pr")
repo_app = typer.Typer(help="Repository metadata.", no_args_is_help=True)
gh_app.add_typer(repo_app, name="repo")
gh_app.add_typer(backlog_app, name="backlog")
gh_app.add_typer(project_app, name="project")
project_app.add_typer(project_item_app, name="item")
gh_app.add_typer(ruleset_app, name="ruleset")
gh_app.add_typer(policy_app, name="policy")
gh_app.add_typer(wf_app, name="wf")
gh_app.add_typer(wf_app, name="workflow")


def _svc(repo: str | None, transport: GhTransportMode = "cli") -> GhService:
    return GhService(repo=repo, transport=transport)


def _project_svc(repo: str | None, transport: GhTransportMode = "cli") -> ProjectService:
    return ProjectService(gh_service=_svc(repo, transport))


def _pr_shortcut(repo: str | None, transport: GhTransportMode = "cli") -> GhPrShortcut:
    return GhPrShortcut(gh=_svc(repo, transport))


def _emit(data: object, fmt: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    typer.echo(f"#{row.get('number', '?')} {row.get('title', row)}")
                else:
                    typer.echo(str(row))
        elif isinstance(data, dict):
            for k, v in data.items():
                typer.echo(f"{k}: {v}")
        else:
            typer.echo(str(data))


def _write_gate(
    operation: str,
    svc: GhService,
    *,
    yes: bool,
    question: str | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    require_write_gate(
        operation,
        svc.snapshot_summary(),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )


@gh_app.callback()
def gh_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="owner/name (default: gh context)"),
    format: str = typer.Option("json", "--format", help="json or table"),
    transport: GhTransportMode = typer.Option("auto", "--transport", help="cli, api, or auto"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
    ctx.obj["format"] = format
    ctx.obj["transport"] = transport


def _ctx_repo(ctx: typer.Context) -> str | None:
    return (ctx.obj or {}).get("repo")


def _ctx_format(ctx: typer.Context) -> str:
    return (ctx.obj or {}).get("format") or "json"


def _ctx_transport(ctx: typer.Context) -> GhTransportMode:
    return (ctx.obj or {}).get("transport") or "cli"


def _policy_block(group: str, subcommand: str | None = None) -> None:
    """Exit with policy message — command exists for discoverability only."""
    op = policy_for_cli_command(group, subcommand)
    if op is None:
        typer.echo("blocked by CLI GitHub policy.", err=True)
        raise typer.Exit(1)
    typer.echo(op.message, err=True)
    raise typer.Exit(1)


def _blocked_handler(group: str, subcommand: str):
    def _cmd(ctx: typer.Context) -> None:  # noqa: ARG001
        _policy_block(group, subcommand)

    return _cmd


# --- Issue read ---


@issue_app.command("list")
def issue_list_cmd(
    ctx: typer.Context,
    state: str = typer.Option("open", "--state"),
    label: list[str] = typer.Option(None, "--label"),
    limit: int = typer.Option(30, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    data = svc.issue_list(state=state, label=label, limit=limit)
    _emit(data, _ctx_format(ctx))


@issue_app.command("view")
def issue_view_cmd(
    ctx: typer.Context,
    number: int,
    comments: bool = typer.Option(False, "--comments"),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    data = svc.issue_view(number, comments=comments)
    _emit(data, _ctx_format(ctx))


@issue_app.command("context")
def issue_context_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    data = svc.issue_context(number)
    _emit(data, _ctx_format(ctx))


@issue_app.command("search")
def issue_search_cmd(
    ctx: typer.Context,
    query: str,
    limit: int = typer.Option(30, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    data = svc.issue_search(query, limit=limit)
    _emit(data, _ctx_format(ctx))


# --- Issue write ---


@issue_app.command("create")
def issue_create_cmd(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    body: str | None = typer.Option(None, "--body"),
    label: list[str] = typer.Option(None, "--label"),
    lane: str | None = typer.Option(None, "--lane", help="Add issue to default project lane."),
    no_project: bool = typer.Option(False, "--no-project", help="Skip project auto-linking."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    auto_link = project_auto_link()
    should_link_project = (not no_project) and (
        lane is not None or (auto_link.enabled and auto_link.on_issue_create)
    )
    extra_lines = [f"title: {title}", f"labels: {label or []}"]
    if should_link_project:
        extra_lines.append(f"project lane: {lane or auto_link.default_lane or '(none)'}")
    _write_gate(
        "gh-issue-create",
        svc,
        yes=yes,
        question=f"Create issue {title!r}?",
        extra_lines=extra_lines,
    )
    data = svc.issue_create(title=title, body_file=body_file, body=body, labels=label)
    if should_link_project:
        project_svc = ProjectService(repo=_ctx_repo(ctx))
        ref = project_svc.default_ref()
        added = project_svc.item_add_url(str(data["url"]), ref)
        item_id = str(added.get("id") or added.get("item", {}).get("id") or added.get("item_id") or "")
        selected_lane = lane or auto_link.default_lane
        if selected_lane and item_id:
            project_svc.item_status(ref, item_id=item_id, status=selected_lane)
        data["project"] = {
            "owner": ref.owner,
            "number": ref.number,
            "project_id": ref.project_id,
            "item_id": item_id,
            "lane": selected_lane,
        }
    _emit(data, _ctx_format(ctx))


@issue_app.command("edit")
def issue_edit_cmd(
    ctx: typer.Context,
    number: int,
    title: str | None = typer.Option(None, "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    add_label: list[str] = typer.Option(None, "--add-label"),
    remove_label: list[str] = typer.Option(None, "--remove-label"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-issue-edit",
        svc,
        yes=yes,
        question=f"Edit issue #{number}?",
        extra_lines=[f"number: {number}", f"title: {title}"],
    )
    svc.issue_edit(
        number,
        title=title,
        body_file=body_file,
        add_labels=add_label,
        remove_labels=remove_label,
    )
    _emit({"number": number, "action": "edit"}, _ctx_format(ctx))


@issue_app.command("close")
def issue_close_cmd(
    ctx: typer.Context,
    number: int,
    comment: str | None = typer.Option(None, "--comment"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    """Close issue (blocked — merge PR in GitHub UI and let auto-close run)."""
    _ = (ctx, number, comment, yes)
    _policy_block("issue", "close")


@issue_app.command("reopen")
def issue_reopen_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-issue-reopen", svc, yes=yes, question=f"Reopen issue #{number}?")
    _emit(svc.issue_reopen(number), _ctx_format(ctx))


@issue_app.command("status")
def issue_status_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.issue_status(), _ctx_format(ctx))


@issue_app.command("delete")
def issue_delete_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-issue-delete", svc, yes=yes, question=f"Delete issue #{number}?")
    svc.issue_delete(number)
    _emit({"number": number, "action": "delete"}, _ctx_format(ctx))


@issue_app.command("comment")
def issue_comment_cmd(
    ctx: typer.Context,
    number: int,
    body: str = typer.Option(..., "--body"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-issue-comment", svc, yes=yes, question=f"Comment on issue #{number}?")
    svc.issue_comment(number, body=body)
    _emit({"number": number, "action": "comment"}, _ctx_format(ctx))


@issue_app.command("batch")
def issue_batch_cmd(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-issue-batch",
        svc,
        yes=yes,
        question=f"Run issue batch from {file}?",
        extra_lines=[f"batch_file: {file}"],
    )
    data = svc.issue_batch(file)
    _emit(data, _ctx_format(ctx))


@issues_app.command("deploy")
def gh_issues_deploy_cmd(
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    require_write_gate(
        "gh-issues-deploy",
        ["target: configured gh.issues.repo", "operation: delete all + recreate"],
        yes=yes or dry_run,
        question="Delete all GitHub issues in configured private repo and recreate from tasks?",
        extra_lines=[f"dry_run: {dry_run}"],
    )
    result = deploy_issues(dry_run=dry_run)
    _emit(result.__dict__, "json")


@issues_app.command("ingest")
def gh_issues_ingest_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    require_write_gate(
        "gh-issues-ingest",
        ["scope: configured task_root", "source: GitHub Issues"],
        question="Ingest GitHub Issues into local task pairs?",
        yes=yes,
    )
    result = ingest_issues()
    _emit(result.__dict__, "json")


@issues_app.command("prune")
def gh_issues_prune_cmd(
    closed_older_than: str = typer.Option("7d", "--closed-older-than"),
    label: list[str] = typer.Option(None, "--label"),
    exclude_label: list[str] = typer.Option(None, "--exclude-label"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    require_write_gate(
        "gh-issues-prune",
        ["target: configured gh.issues.repo", "operation: filtered issue delete"],
        yes=yes or dry_run,
        question=f"Delete closed issues older than {closed_older_than}?",
        extra_lines=[f"dry_run: {dry_run}", f"labels: {label or []}"],
    )
    result = prune_issues(
        closed_older_than=closed_older_than,
        include_labels=label or [],
        exclude_labels=exclude_label or [],
        dry_run=dry_run,
    )
    _emit(result.__dict__, "json")


# --- Label ---


@label_app.command("list")
def label_list_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.label_list(), _ctx_format(ctx))


@label_app.command("create")
def label_create_cmd(
    ctx: typer.Context,
    name: str,
    color: str = typer.Option("ededed", "--color"),
    description: str = typer.Option("", "--description"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-label-create", svc, yes=yes, question=f"Create label {name!r}?")
    svc.label_create(name, color=color, description=description)
    _emit({"name": name, "action": "create"}, _ctx_format(ctx))


@label_app.command("delete")
def label_delete_cmd(
    ctx: typer.Context,
    name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-label-delete", svc, yes=yes, question=f"Delete label {name!r}?")
    svc.label_delete(name)
    _emit({"name": name, "action": "delete"}, _ctx_format(ctx))


@label_app.command("sync")
def label_sync_cmd(
    ctx: typer.Context,
    manifest: Path = typer.Option(..., "--manifest"),
    prune_orphans: bool = typer.Option(False, "--prune-orphans"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-label-sync",
        svc,
        yes=yes,
        question=f"Sync labels from {manifest}?",
        extra_lines=[f"prune_orphans: {prune_orphans}"],
    )
    data = svc.label_sync(manifest, prune_orphans=prune_orphans)
    _emit(data, _ctx_format(ctx))


# --- PR ---


@pr_app.callback(invoke_without_command=True)
def pr_root(
    ctx: typer.Context,
    title: str = typer.Option(".", "--title", help="PR title for shortcut mode."),
    body: str = typer.Option("", "--body", help="PR body for shortcut mode."),
    template: str | None = typer.Option(None, "--template", help="Use a PR template by name."),
    no_push: bool = typer.Option(False, "--no-push", help="Create PR without publishing first."),
    allow_main: bool = typer.Option(False, "--allow-main", help="Allow PR shortcut from main."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    """Shortcut: push if needed, then create a PR with quick defaults."""
    if ctx.invoked_subcommand is not None:
        return
    shortcut = _pr_shortcut(_ctx_repo(ctx), _ctx_transport(ctx))
    allow_main = _interactive_allow_main(shortcut.git, allow_main=allow_main, yes=yes)
    try:
        plan = shortcut.plan(
            title=title,
            body=body,
            template=template,
            no_push=no_push,
            allow_main=allow_main,
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if plan.no_push and plan.needs_push:
        typer.echo(
            "Branch is not ready for PR creation with --no-push. "
            "Publish it first or rerun without --no-push.",
            err=True,
        )
        raise typer.Exit(1)
    require_write_gate(
        "gh-pr",
        shortcut.gh.snapshot_summary(),
        question=f"Create PR on {plan.branch!r}?",
        yes=yes,
        extra_lines=plan.summary_lines(),
    )
    try:
        data = shortcut.create(plan, yes=True)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _emit(data, _ctx_format(ctx))


@pr_app.command("list")
def pr_list_cmd(
    ctx: typer.Context,
    state: str = typer.Option("open", "--state"),
    limit: int = typer.Option(30, "--limit"),
    head: str | None = typer.Option(None, "--head"),
    base: str | None = typer.Option(None, "--base"),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.pr_list(state=state, limit=limit, head=head, base=base), _ctx_format(ctx))


@pr_app.command("view")
def pr_view_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.pr_view(number), _ctx_format(ctx))


@pr_app.command("diff")
def pr_diff_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    text = svc.pr_diff_stat(number)
    if _ctx_format(ctx) == "json":
        _emit({"number": number, "stat": text}, "json")
    else:
        typer.echo(text)


@pr_app.command("status")
def pr_status_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.pr_status(), _ctx_format(ctx))


@pr_app.command("create")
def pr_create_cmd(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    body: str | None = typer.Option(None, "--body"),
    base: str | None = typer.Option(None, "--base"),
    head: str | None = typer.Option(None, "--head"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-create", svc, yes=yes, question=f"Create PR {title!r}?")
    data = svc.pr_create(title=title, body_file=body_file, body=body, base=base, head=head)
    _emit(data, _ctx_format(ctx))


@pr_app.command("upsert")
def pr_upsert_cmd(
    ctx: typer.Context,
    branch: str = typer.Option(..., "--branch", help="Fixed branch to push and reuse for the PR."),
    title: str = typer.Option(..., "--title"),
    body: str = typer.Option("", "--body"),
    base: str = typer.Option("main", "--base"),
    message: str = typer.Option(..., "--message", help="Commit message for staged changes."),
    close_when_clean: bool = typer.Option(
        False,
        "--close-when-clean",
        help="Close the existing branch PR when there are no local changes.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    shortcut = _pr_shortcut(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-pr-upsert",
        shortcut.gh,
        yes=yes,
        question=f"Commit, push, and upsert PR for {branch!r}?",
        extra_lines=[
            f"branch: {branch}",
            f"base: {base}",
            f"title: {title}",
            f"close_when_clean: {close_when_clean}",
        ],
    )
    data = shortcut.upsert_branch_pr(
        branch=branch,
        title=title,
        body=body,
        base=base,
        message=message,
        close_when_clean=close_when_clean,
    )
    _emit(data, _ctx_format(ctx))


@pr_app.command("edit")
def pr_edit_cmd(
    ctx: typer.Context,
    number: int,
    title: str | None = typer.Option(None, "--title"),
    body_file: Path | None = typer.Option(None, "--body-file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-edit", svc, yes=yes, question=f"Edit PR #{number}?")
    svc.pr_edit(number, title=title, body_file=body_file)
    _emit({"number": number, "action": "edit"}, _ctx_format(ctx))


@pr_app.command("comment")
def pr_comment_cmd(
    ctx: typer.Context,
    number: int,
    body: str = typer.Option(..., "--body"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-comment", svc, yes=yes, question=f"Comment on PR #{number}?")
    svc.pr_comment(number, body=body)
    _emit({"number": number, "action": "comment"}, _ctx_format(ctx))


@pr_app.command("close")
def pr_close_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-close", svc, yes=yes, question=f"Close PR #{number}?")
    svc.pr_close(number)
    _emit({"number": number, "action": "close"}, _ctx_format(ctx))


@pr_app.command("reopen")
def pr_reopen_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-reopen", svc, yes=yes, question=f"Reopen PR #{number}?")
    _emit(svc.pr_reopen(number), _ctx_format(ctx))


@pr_app.command("checks")
def pr_checks_cmd(ctx: typer.Context, number: int) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.pr_checks(number), _ctx_format(ctx))


@pr_app.command("review")
def pr_review_cmd(
    ctx: typer.Context,
    number: int,
    approve: bool = typer.Option(False, "--approve"),
    request_changes: bool = typer.Option(False, "--request-changes"),
    comment: bool = typer.Option(False, "--comment"),
    body: str = typer.Option("", "--body"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    if sum(bool(value) for value in (approve, request_changes, comment)) != 1:
        typer.echo("Pass exactly one of --approve, --request-changes, or --comment", err=True)
        raise typer.Exit(2)
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-review", svc, yes=yes, question=f"Submit review on PR #{number}?")
    _emit(
        svc.pr_review(
            number,
            approve=approve,
            request_changes=request_changes,
            comment=comment,
            body=body,
        ),
        _ctx_format(ctx),
    )


@pr_app.command("ready")
def pr_ready_cmd(
    ctx: typer.Context,
    number: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-pr-ready", svc, yes=yes, question=f"Mark PR #{number} ready for review?")
    _emit(svc.pr_ready(number), _ctx_format(ctx))


@pr_app.command("merge")
def pr_merge_cmd(
    ctx: typer.Context,
    number: int,
    merge_method: str = typer.Option("merge", "--merge-method"),
    delete_branch: bool = typer.Option(False, "--delete-branch"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Ignored — merge blocked by policy."),
) -> None:
    """Merge PR (blocked — use GitHub UI or auto-merge)."""
    _ = (ctx, number, merge_method, delete_branch, yes)
    _policy_block("pr", "merge")


# --- Backlog ---


@backlog_app.command("tree")
def backlog_tree_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.backlog_tree(), _ctx_format(ctx))


@backlog_app.command("organize")
def backlog_organize_cmd(ctx: typer.Context) -> None:
    """Epic issues, sorted subissues (step 1..N), priority explanations, readiness."""
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.backlog_organize(), _ctx_format(ctx))


@backlog_app.command("levels")
def backlog_levels_cmd(ctx: typer.Context) -> None:
    """Show priority:1..N label scale with explanations (no GitHub Projects)."""
    data = {"levels": load_priority_levels()}
    _emit(data, _ctx_format(ctx))


@backlog_app.command("next")
def backlog_next_cmd(ctx: typer.Context) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    data = svc.backlog_next()
    if data is None:
        if _ctx_format(ctx) == "json":
            _emit({"next": None}, "json")
        else:
            typer.echo("No open subissue found.")
        raise typer.Exit(0)
    _emit(data, _ctx_format(ctx))


@backlog_app.command("resequence")
def backlog_resequence_cmd(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-backlog-resequence",
        svc,
        yes=yes,
        question=f"Resequence titles from {file}?",
    )
    data = svc.backlog_resequence(file)
    _emit(data, _ctx_format(ctx))


@repo_app.command("list")
def repo_list_cmd(
    ctx: typer.Context,
    owner: str = typer.Option("gardusig", "--owner", help="GitHub user or org"),
    limit: int = typer.Option(100, "--limit"),
    visibility: str = typer.Option("public", "--visibility", help="public, private, or all"),
) -> None:
    """List repositories for an owner (default: gardusig public repos)."""
    vis = None if visibility == "all" else visibility
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.repo_list(owner=owner, limit=limit, visibility=vis), _ctx_format(ctx))


@repo_app.command("view")
def repo_view_cmd(
    ctx: typer.Context,
    fields: str = typer.Option(
        "nameWithOwner,owner,issueTemplates,pullRequestTemplates",
        "--json-fields",
        help="Comma-separated gh repo view --json fields",
    ),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.repo_view(fields=fields), _ctx_format(ctx))


@repo_app.command("readme-sync")
def repo_readme_sync_cmd(
    readme: Path = typer.Option(..., "--readme", help="Profile README path to update"),
    owner: str = typer.Option("gardusig", "--owner"),
    limit: int = typer.Option(100, "--limit"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Refresh auto-sync repo list markers in gardusig/gardusig README.md."""
    from src.services.gh_repo_readme import sync_profile_readme

    updated, repos = sync_profile_readme(readme, owner=owner, limit=limit)
    current = readme.read_text(encoding="utf-8")
    if updated == current:
        typer.echo(f"readme ok ({len(repos)} repos)")
        return
    if dry_run:
        typer.echo(updated)
        return
    readme.write_text(updated, encoding="utf-8")
    typer.echo(f"updated {readme} ({len(repos)} repos)")


# --- GitHub Projects ---


@project_app.command("list")
def project_list_cmd(
    ctx: typer.Context,
    owner: str = typer.Option("gardusig", "--owner"),
    limit: int = typer.Option(30, "--limit"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.project_list(owner=owner, limit=limit), _ctx_format(ctx))


@project_app.command("view")
def project_view_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    _emit(svc.project_view(ref.require_number(), owner=ref.owner), _ctx_format(ctx))


@project_app.command("create")
def project_create_cmd(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner)
    require_write_gate(
        "gh-project-create",
        svc.snapshot_summary(ref),
        yes=yes,
        question=f"Create GitHub Project {title!r}?",
    )
    _emit(svc.project_create(owner=ref.owner, title=title), _ctx_format(ctx))


@project_app.command("edit")
def project_edit_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
    title: str | None = typer.Option(None, "--title"),
    readme: str | None = typer.Option(None, "--readme"),
    visibility: str | None = typer.Option(None, "--visibility"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    require_write_gate(
        "gh-project-edit",
        svc.snapshot_summary(ref),
        yes=yes,
        question=f"Edit GitHub Project {ref.require_number()}?",
        extra_lines=[f"title: {title}", f"visibility: {visibility}"],
    )
    data = svc.project_edit(
        ref.require_number(),
        owner=ref.owner,
        title=title,
        readme=readme,
        visibility=visibility,
    )
    _emit(data, _ctx_format(ctx))


@project_app.command("delete")
def project_delete_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    require_write_gate(
        "gh-project-delete",
        svc.snapshot_summary(ref),
        yes=yes,
        question=f"Delete GitHub Project {ref.require_number()}?",
    )
    _emit(svc.project_delete(ref.require_number(), owner=ref.owner), _ctx_format(ctx))


@project_item_app.command("list")
def project_item_list_cmd(
    ctx: typer.Context,
    number: int | None = typer.Argument(None),
    owner: str | None = typer.Option(None, "--owner"),
    limit: int = typer.Option(100, "--limit"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.item_list(svc.ref(owner=owner, number=number), limit=limit), _ctx_format(ctx))


@project_item_app.command("view")
def project_item_view_cmd(
    ctx: typer.Context,
    id: str = typer.Option(..., "--id"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.item_view(id, svc.ref(owner=owner, number=number)), _ctx_format(ctx))


@project_item_app.command("add")
def project_item_add_cmd(
    ctx: typer.Context,
    url: str | None = typer.Option(None, "--url"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    lane: str | None = typer.Option(None, "--lane"),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    target = url or (f"issue #{issue}" if issue is not None else f"pr #{pr}" if pr is not None else "item")
    require_write_gate("gh-project-item-add", svc.snapshot_summary(ref), yes=yes, question=f"Add {target} to project?")
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


@project_item_app.command("edit")
def project_item_edit_cmd(
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
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    require_write_gate("gh-project-item-edit", svc.snapshot_summary(ref), yes=yes, question=f"Edit project item {item_id}?")
    _emit(
        svc.item_set(ref, item_id=item_id, field=field, value=value, value_kind=value_kind),
        _ctx_format(ctx),
    )


@project_item_app.command("delete")
def project_item_delete_cmd(
    ctx: typer.Context,
    id: str | None = typer.Option(None, "--id"),
    issue: int | None = typer.Option(None, "--issue"),
    pr: int | None = typer.Option(None, "--pr"),
    archive: bool = typer.Option(False, "--archive", help="Archive instead of delete."),
    number: int | None = typer.Option(None, "--project"),
    owner: str | None = typer.Option(None, "--owner"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    svc = _project_svc(_ctx_repo(ctx), _ctx_transport(ctx))
    ref = svc.ref(owner=owner, number=number)
    item = svc.find_item(ref, item_id=id, issue=issue, pr=pr)
    item_id = str(item.get("id") or id)
    require_write_gate("gh-project-item-delete", svc.snapshot_summary(ref), yes=yes, question=f"Remove project item {item_id}?")
    data = svc.item_archive(ref, item_id=item_id) if archive else svc.item_delete(ref, item_id=item_id)
    _emit(data, _ctx_format(ctx))


# --- Blocked GitHub surfaces (exist in CLI, always error) ---


@policy_app.command("list")
def policy_list_cmd(ctx: typer.Context) -> None:
    """List gh operations blocked by CLI policy and their alternatives."""
    _emit(blocked_operations_catalog(), _ctx_format(ctx))


for _sub in ("list", "view", "create", "edit", "delete"):
    ruleset_app.command(
        _sub,
        help="Blocked — configure rulesets in the GitHub UI.",
    )(_blocked_handler("ruleset", _sub))
