"""GitHub (`gh`) subcommands — JSON-first, write gates."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from src.commands.git import _interactive_allow_main
from src.internal.write.gate import require_write_gate
from src.providers.gh_transport import GhTransportMode
from src.services.gh_policy import (
    blocked_operations_catalog,
    policy_for_cli_command,
)
from src.services.gh_pr_shortcut import GhPrShortcut
from src.services.gh_service import GhService

gh_app = typer.Typer(help="GitHub via gh — issues, branches, PRs.", no_args_is_help=True)
issue_app = typer.Typer(help="Issue read/write.", no_args_is_help=True)
branch_app = typer.Typer(help="Remote branch read/write.", no_args_is_help=True)
pr_app = typer.Typer(help="Pull request read/write.", no_args_is_help=False)
ruleset_app = typer.Typer(
    help="GitHub Rulesets (blocked — use GitHub UI).",
    no_args_is_help=True,
)
policy_app = typer.Typer(help="CLI GitHub policy.", no_args_is_help=True)

gh_app.add_typer(issue_app, name="issue")
gh_app.add_typer(branch_app, name="branch")
gh_app.add_typer(pr_app, name="pr")
gh_app.add_typer(ruleset_app, name="ruleset")
gh_app.add_typer(policy_app, name="policy")


def _svc(repo: str | None, transport: GhTransportMode = "cli") -> GhService:
    return GhService(repo=repo, transport=transport)


def _pr_shortcut(repo: str | None, transport: GhTransportMode = "cli") -> GhPrShortcut:
    return GhPrShortcut(gh=_svc(repo, transport))


def _emit(data: object, fmt: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    if "number" in row or "title" in row:
                        typer.echo(f"#{row.get('number', '?')} {row.get('title', row)}")
                    elif "name" in row:
                        typer.echo(str(row["name"]))
                    else:
                        typer.echo(str(row))
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
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate(
        "gh-issue-create",
        svc,
        yes=yes,
        question=f"Create issue {title!r}?",
        extra_lines=[f"title: {title}", f"labels: {label or []}"],
    )
    data = svc.issue_create(title=title, body_file=body_file, body=body, labels=label)
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



# --- Branch ---


@branch_app.command("list")
def branch_list_cmd(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit"),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.branch_list(limit=limit), _ctx_format(ctx))


@branch_app.command("view")
def branch_view_cmd(ctx: typer.Context, name: str) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _emit(svc.branch_view(name), _ctx_format(ctx))


@branch_app.command("delete")
def branch_delete_cmd(
    ctx: typer.Context,
    name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
) -> None:
    svc = _svc(_ctx_repo(ctx), _ctx_transport(ctx))
    _write_gate("gh-branch-delete", svc, yes=yes, question=f"Delete remote branch {name!r}?")
    svc.branch_delete(name)
    _emit({"branch": name, "action": "delete"}, _ctx_format(ctx))


@branch_app.command("pr")
def branch_pr_cmd(ctx: typer.Context, name: str) -> None:
    shortcut = _pr_shortcut(_ctx_repo(ctx), _ctx_transport(ctx))
    pr = shortcut.find_open_pr_for_branch(name)
    if pr is None:
        _emit({"branch": name, "pull_request": None}, _ctx_format(ctx))
        return
    _emit({"branch": name, "pull_request": pr}, _ctx_format(ctx))


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
