"""Dispatch centralized github-pipelines workflows."""

from __future__ import annotations

import json
import subprocess
from argparse import Namespace
from pathlib import Path

import typer

from src.services.pipeline_runtime import resolve_config, run_docker_job, run_task_action

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
    body = json.dumps({"event_type": family, "client_payload": payload})
    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/gardusig/github-pipelines/dispatches",
            "--input",
            "-",
        ],
        input=body,
        text=True,
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
    app_src: Path | None = typer.Option(None, "--app-src"),
    selective_base: str = typer.Option("", "--selective-base"),
    selective_head: str = typer.Option("", "--selective-head"),
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
    if app_src is not None:
        args.extend(["--app-src", str(app_src)])
    if selective_base:
        args.extend(["--selective-base", selective_base])
    if selective_head:
        args.extend(["--selective-head", selective_head])
    _run_pipeline_runtime(resolve_config, _namespace_from_args(args))


@docker_app.command("run")
def docker_run_cmd(
    job_json: str = typer.Option(..., "--job-json"),
    pipeline_src: Path = typer.Option(..., "--pipeline-src"),
    app_src: Path = typer.Option(..., "--app-src"),
    tag_prefix: str = typer.Option("pipeline", "--tag-prefix"),
    release_version: str = typer.Option("", "--release-version"),
    pages_output: Path = typer.Option(Path("publish-pages"), "--pages-output"),
) -> None:
    _run_pipeline_runtime(
        run_docker_job,
        Namespace(
            job_json=job_json,
            pipeline_src=pipeline_src,
            app_src=app_src,
            tag_prefix=tag_prefix,
            release_version=release_version,
            pages_output=pages_output,
        ),
    )


@task_app.command("run")
def task_run_cmd(
    command_json: str = typer.Option(..., "--command-json"),
    env_json: str = typer.Option("{}", "--env-json"),
    repo_dir: Path = typer.Option(..., "--repo-dir"),
) -> None:
    _run_pipeline_runtime(run_task_action, Namespace(command_json=command_json, env_json=env_json, repo_dir=repo_dir))


def _run_pipeline_runtime(func, args: Namespace) -> None:
    try:
        func(args)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if exc.code and not isinstance(exc.code, int):
            typer.echo(str(exc.code), err=True)
        raise typer.Exit(code) from exc


def _namespace_from_args(args: list[str]) -> Namespace:
    values = {args[index].removeprefix("--").replace("-", "_"): args[index + 1] for index in range(0, len(args), 2)}
    values["pipeline_src"] = Path(values["pipeline_src"])
    return Namespace(**values)
