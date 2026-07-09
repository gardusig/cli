"""GitHub Actions workflow wrappers (`cli gh wf` / `cli gh workflow`)."""

from __future__ import annotations

import sys

import typer

from src.utils.process import run_gh

wf_app = typer.Typer(help="GitHub Actions workflows (wf).", no_args_is_help=True)
run_app = typer.Typer(help="Workflow runs.", invoke_without_command=True, no_args_is_help=False)


def _repo_args(repo: str | None) -> list[str]:
    return ["-R", repo] if repo else []


def _gh(args: list[str], *, check: bool = True) -> int:
    result = run_gh(args, check=False)
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
    if check and result.returncode != 0:
        raise typer.Exit(result.returncode)
    return result.returncode


@wf_app.command("list")
def wf_list_cmd(
    repo: str | None = typer.Option(None, "--repo", "-R", help="owner/name"),
    limit: int = typer.Option(50, "--limit"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List workflows (`gh workflow list`)."""
    args = ["workflow", "list", *_repo_args(repo), "--limit", str(limit)]
    if json_output:
        args.append("--json")
    _gh(args)


@wf_app.command("view")
def wf_view_cmd(
    workflow: str = typer.Argument(..., help="Workflow name, ID, or filename."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    yaml_output: bool = typer.Option(False, "--yaml"),
) -> None:
    """View a workflow (`gh workflow view`)."""
    args = ["workflow", "view", workflow, *_repo_args(repo)]
    if yaml_output:
        args.append("--yaml")
    _gh(args)


@wf_app.command("enable")
def wf_enable_cmd(
    workflow: str = typer.Argument(..., help="Workflow ID or filename."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
) -> None:
    _gh(["workflow", "enable", workflow, *_repo_args(repo)])


@wf_app.command("disable")
def wf_disable_cmd(
    workflow: str = typer.Argument(..., help="Workflow ID or filename."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
) -> None:
    _gh(["workflow", "disable", workflow, *_repo_args(repo)])


@run_app.callback()
def run_group_callback(
    ctx: typer.Context,
    workflow: str | None = typer.Argument(
        None,
        help="Workflow file or ID — starts a run when no run subcommand is given.",
    ),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    field: list[str] = typer.Option([], "--field", "-f", help="workflow_dispatch input (key=value)."),
    ref: str | None = typer.Option(None, "--ref", help="Branch or tag for workflow_dispatch."),
) -> None:
    """Run instances, or start a workflow when given a workflow file/id."""
    if ctx.invoked_subcommand is not None:
        return
    if not workflow:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)
    args = ["workflow", "run", workflow, *_repo_args(repo)]
    if ref:
        args.extend(["--ref", ref])
    for item in field:
        args.extend(["-f", item])
    raise typer.Exit(_gh(args))


@run_app.command("list")
def run_list_cmd(
    repo: str | None = typer.Option(None, "--repo", "-R"),
    workflow: str | None = typer.Option(None, "--workflow", "-w"),
    branch: str | None = typer.Option(None, "--branch", "-b"),
    limit: int = typer.Option(20, "--limit"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List workflow runs (`gh run list`)."""
    args = ["run", "list", *_repo_args(repo), "--limit", str(limit)]
    if workflow:
        args.extend(["--workflow", workflow])
    if branch:
        args.extend(["--branch", branch])
    if json_output:
        args.append("--json")
    _gh(args)


@run_app.command("view")
def run_view_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    job: str | None = typer.Option(None, "--job", "-j", help="Job ID."),
    verbose: bool = typer.Option(True, "--verbose/--no-verbose", "-v"),
    log: bool = typer.Option(False, "--log"),
    web: bool = typer.Option(False, "--web"),
) -> None:
    """View a workflow run (`gh run view`)."""
    args = ["run", "view", run_id, *_repo_args(repo)]
    if job:
        args.extend(["--job", job])
    if verbose:
        args.append("--verbose")
    if log:
        args.append("--log")
    if web:
        args.append("--web")
    _gh(args)


@run_app.command("failed")
def run_failed_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    job: str | None = typer.Option(None, "--job", "-j"),
    exit_status: bool = typer.Option(True, "--exit-status/--no-exit-status"),
) -> None:
    """Print logs for failed steps (`gh run view --log-failed`)."""
    args = ["run", "view", run_id, *_repo_args(repo), "--log-failed"]
    if job:
        args.extend(["--job", job])
    if exit_status:
        args.append("--exit-status")
    code = _gh(args, check=False)
    raise typer.Exit(code)


@run_app.command("watch")
def run_watch_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    exit_status: bool = typer.Option(False, "--exit-status"),
) -> None:
    """Watch a run until it completes (`gh run watch`)."""
    args = ["run", "watch", run_id, *_repo_args(repo)]
    if exit_status:
        args.append("--exit-status")
    _gh(args)


@run_app.command("cancel")
def run_cancel_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
) -> None:
    _gh(["run", "cancel", run_id, *_repo_args(repo)])


@run_app.command("rerun")
def run_rerun_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    failed: bool = typer.Option(False, "--failed", help="Rerun only failed jobs."),
) -> None:
    args = ["run", "rerun", run_id, *_repo_args(repo)]
    if failed:
        args.append("--failed")
    _gh(args)


@run_app.command("delete")
def run_delete_cmd(
    run_id: str = typer.Argument(..., help="Run ID."),
    repo: str | None = typer.Option(None, "--repo", "-R"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    args = ["run", "delete", run_id, *_repo_args(repo)]
    if yes:
        args.append("--yes")
    _gh(args)


wf_app.add_typer(run_app, name="run")
