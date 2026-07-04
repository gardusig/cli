"""Dispatch centralized github-pipelines workflows."""

from __future__ import annotations

import json
import subprocess

import typer

pipeline_app = typer.Typer(help="Dispatch centralized workflows.", no_args_is_help=True)


@pipeline_app.command("run")
def run_cmd(
    family: str,
    repo: str,
    action: str | None = typer.Option(None, "--action"),
    job: str | None = typer.Option(None, "--job"),
    ref: str = typer.Option("main", "--ref"),
    repository: str | None = typer.Option(None, "--repository"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """POST repository_dispatch to gardusig/github-pipelines."""
    payload = {
        "repo_slug": repo,
        "repository": repository or f"gardusig/{repo}",
        "ref": ref,
        "dry_run": dry_run,
    }
    if action:
        payload["action"] = action
    if job:
        payload["job"] = job
    subprocess.run(
        [
            "gh",
            "api",
            "repos/gardusig/github-pipelines/dispatches",
            "-F",
            f"event_type={family}",
            "-F",
            f"client_payload:={json.dumps(payload)}",
        ],
        check=True,
    )
    typer.echo(f"dispatched {family} for {repo}")
