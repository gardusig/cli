"""Dispatch centralized github-pipelines workflows."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer

pipeline_app = typer.Typer(help="Dispatch centralized workflows.", no_args_is_help=True)
config_app = typer.Typer(help="Resolve pipeline workflow config.", no_args_is_help=True)
docker_app = typer.Typer(help="Run pipeline Docker jobs.", no_args_is_help=True)
task_app = typer.Typer(help="Run resolved task actions.", no_args_is_help=True)

pipeline_app.add_typer(config_app, name="config")
pipeline_app.add_typer(docker_app, name="docker")
pipeline_app.add_typer(task_app, name="task")


@pipeline_app.command("run")
def run_cmd(
    family: str,
    repo: str,
    action: str | None = typer.Option(None, "--action"),
    job: str | None = typer.Option(None, "--job"),
    pipeline: str | None = typer.Option(None, "--pipeline"),
    ref: str = typer.Option("main", "--ref"),
    sha: str | None = typer.Option(None, "--sha"),
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
    if pipeline:
        payload["pipeline"] = pipeline
    if sha:
        payload["sha"] = sha
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


@config_app.command("resolve")
def config_resolve_cmd(
    family: str = typer.Option(..., "--family"),
    pipeline_src: Path = typer.Option(Path("."), "--pipeline-src"),
    repo_slug: str = typer.Option("", "--repo-slug"),
    pipeline: str = typer.Option("", "--pipeline"),
    repository: str = typer.Option("", "--repository"),
    ref: str = typer.Option("", "--ref"),
    sha: str = typer.Option("", "--sha"),
    job: str = typer.Option("", "--job"),
    action: str = typer.Option("", "--action"),
    dry_run: str = typer.Option("", "--dry-run"),
) -> None:
    args = [
        "--family",
        family,
        "--pipeline-src",
        str(pipeline_src),
        "--repo-slug",
        repo_slug,
        "--pipeline",
        pipeline,
        "--repository",
        repository,
        "--ref",
        ref,
        "--sha",
        sha,
        "--job",
        job,
        "--action",
        action,
        "--dry-run",
        dry_run,
    ]
    _run_pipeline_script("config-resolve.sh", args)


@docker_app.command("run")
def docker_run_cmd(
    job_json: str = typer.Option(..., "--job-json"),
    pipeline_src: Path = typer.Option(..., "--pipeline-src"),
    app_src: Path = typer.Option(..., "--app-src"),
    tag_prefix: str = typer.Option("pipeline", "--tag-prefix"),
    release_version: str = typer.Option("", "--release-version"),
    pages_output: Path = typer.Option(Path("publish-pages"), "--pages-output"),
) -> None:
    _run_pipeline_script(
        "docker-run.sh",
        [
            "--job-json",
            job_json,
            "--pipeline-src",
            str(pipeline_src),
            "--app-src",
            str(app_src),
            "--tag-prefix",
            tag_prefix,
            "--release-version",
            release_version,
            "--pages-output",
            str(pages_output),
        ],
    )


@task_app.command("run")
def task_run_cmd(
    command_json: str = typer.Option(..., "--command-json"),
    env_json: str = typer.Option("{}", "--env-json"),
    repo_dir: Path = typer.Option(..., "--repo-dir"),
) -> None:
    _run_pipeline_script(
        "task-run.sh",
        ["--command-json", command_json, "--env-json", env_json, "--repo-dir", str(repo_dir)],
    )


def _run_pipeline_script(script_name: str, args: list[str]) -> None:
    script = _scripts_root() / "pipeline" / script_name
    if not script.is_file():
        typer.echo(f"Missing script: {script}", err=True)
        raise typer.Exit(1)
    env = os.environ.copy()
    env.setdefault("CLI_BIN", f"{sys.executable} -m src")
    result = subprocess.run(["bash", str(script), *args], env=env, check=False)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


def _scripts_root() -> Path:
    source_root = Path(__file__).resolve().parents[1] / "scripts"
    if source_root.is_dir():
        return source_root
    return Path(sys.prefix) / "share" / "gardusig-cli" / "scripts"
