"""Deploy — dispatch hub CI and operator lanes."""

from __future__ import annotations

import json

import typer

from src.internal.write.gate import require_write_gate
from src.services.pipeline_dispatch import dispatch_repository_event

deploy_app = typer.Typer(
    help="Dispatch hub CI and operator lanes (github-pipelines).",
    no_args_is_help=True,
)


def _repo_slug(repo: str, repository: str | None) -> tuple[str, str]:
    slug = repo.strip()
    full = (repository or f"gardusig/{slug}").strip()
    return slug, full


def _dispatch(
    event_type: str,
    payload: dict[str, object],
    *,
    dry_run: bool,
    yes: bool,
    gate: str,
    summary: list[str],
) -> None:
    if not dry_run:
        require_write_gate(gate, summary, yes=yes)
    result = dispatch_repository_event(event_type, payload, dry_run=dry_run)
    typer.echo(json.dumps(result, indent=2) if dry_run else f"dispatched {event_type}")


@deploy_app.command("pull-request")
def deploy_pull_request_cmd(
    repo: str = typer.Argument(..., help="Repo slug (e.g. python-cli)."),
    ref: str = typer.Option("main", "--ref"),
    sha: str | None = typer.Option(None, "--sha"),
    repository: str | None = typer.Option(None, "--repository"),
    pipeline: str | None = typer.Option(None, "--pipeline"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Dispatch the full pull-request Docker pipeline for an app repo."""
    slug, full = _repo_slug(repo, repository)
    payload: dict[str, object] = {
        "repo_slug": slug,
        "repository": full,
        "ref": ref,
        "dry_run": dry_run,
    }
    if pipeline:
        payload["pipeline"] = pipeline
    if sha:
        payload["sha"] = sha
    _dispatch(
        "pull-request",
        payload,
        dry_run=dry_run,
        yes=yes,
        gate="deploy-pull-request",
        summary=[f"repo: {full}", f"ref: {ref}", f"sha: {sha or ''}"],
    )


@deploy_app.command("operator")
def deploy_operator_cmd(
    lane: str = typer.Argument(..., help="Operator lane: test, plan, execute, review."),
    repository: str = typer.Option(..., "--repository", help="owner/name"),
    ref: str = typer.Option(..., "--ref"),
    sha: str | None = typer.Option(None, "--sha"),
    issue: str | None = typer.Option(None, "--issue"),
    pr: str | None = typer.Option(None, "--pr"),
    base: str = typer.Option("main", "--base"),
    package_limit: str = typer.Option("4", "--package-limit"),
    pipeline: str | None = typer.Option(None, "--pipeline"),
    handoff_pr: bool = typer.Option(False, "--handoff-pr"),
    comment: bool = typer.Option(True, "--comment/--no-comment"),
    comment_yes: bool = typer.Option(False, "--comment-yes"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Dispatch operator-dispatch.yml (test, plan, execute, review)."""
    lane_norm = lane.strip().lower()
    if lane_norm not in {"test", "plan", "execute", "review"}:
        typer.echo("lane must be one of: test, plan, execute, review", err=True)
        raise typer.Exit(1)
    if lane_norm in {"plan", "execute"} and not issue:
        typer.echo("--issue is required for plan and execute lanes", err=True)
        raise typer.Exit(1)
    if lane_norm == "review" and not pr:
        typer.echo("--pr is required for review lane", err=True)
        raise typer.Exit(1)
    if lane_norm == "execute" and not yes:
        typer.echo("execute lane requires --yes", err=True)
        raise typer.Exit(1)

    payload: dict[str, object] = {
        "lane": lane_norm,
        "repository": repository,
        "ref": ref,
        "base": base,
        "package_limit": package_limit,
        "comment": "true" if comment else "false",
        "comment_yes": "true" if comment_yes else "false",
        "handoff_pr": "true" if handoff_pr else "false",
        "yes": "true" if yes else "false",
    }
    if sha:
        payload["sha"] = sha
    if issue:
        payload["issue"] = issue
    if pr:
        payload["pr"] = pr
    if pipeline:
        payload["pipeline"] = pipeline

    _dispatch(
        "operator",
        payload,
        dry_run=dry_run,
        yes=yes,
        gate="deploy-operator",
        summary=[f"lane: {lane_norm}", f"repository: {repository}", f"ref: {ref}"],
    )


@deploy_app.command("release")
def deploy_release_cmd(
    repo: str = typer.Argument(..., help="Repo slug (e.g. python-cli)."),
    ref: str = typer.Option("main", "--ref", help="Git ref or tag (e.g. v1.0.2)."),
    repository: str | None = typer.Option(None, "--repository"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Dispatch hub release workflow for an app repo."""
    slug, full = _repo_slug(repo, repository)
    payload: dict[str, object] = {
        "repo_slug": slug,
        "repository": full,
        "ref": ref,
        "dry_run": dry_run,
    }
    _dispatch(
        "release",
        payload,
        dry_run=dry_run,
        yes=yes,
        gate="deploy-release",
        summary=[f"repo: {full}", f"ref: {ref}"],
    )
