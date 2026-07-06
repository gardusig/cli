from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

MAX_STAGES = 8


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src.services.pipeline_runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("config-resolve")
    resolve.add_argument("--family", required=True, choices=["pull-request", "repo-review", "release", "tasks"])
    resolve.add_argument("--pipeline-src", type=Path, default=Path("."))
    resolve.add_argument("--repo-slug", default="")
    resolve.add_argument("--pipeline", default="")
    resolve.add_argument("--repository", default="")
    resolve.add_argument("--ref", default="")
    resolve.add_argument("--sha", default="")
    resolve.add_argument("--job", default="")
    resolve.add_argument("--action", default="")
    resolve.add_argument("--dry-run", default="")
    resolve.add_argument("--app-src", type=Path, default=None)
    resolve.add_argument("--selective-base", default="")
    resolve.add_argument("--selective-head", default="")
    resolve.add_argument(
        "--force-full-suite",
        action="store_true",
        help="Ignore selective package matrix; run full-suite PR jobs (ci:full).",
    )

    docker = sub.add_parser("docker-run")
    docker.add_argument("--job-json", required=True)
    docker.add_argument("--pipeline-src", type=Path, required=True)
    docker.add_argument("--app-src", type=Path, required=True)
    docker.add_argument("--tag-prefix", default="pipeline")
    docker.add_argument("--release-version", default="")
    docker.add_argument("--pages-output", type=Path, default=Path("publish-pages"))

    task = sub.add_parser("task-run")
    task.add_argument("--command-json", required=True)
    task.add_argument("--env-json", default="{}")
    task.add_argument("--repo-dir", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "config-resolve":
        resolve_config(args)
    elif args.command == "docker-run":
        run_docker_job(args)
    elif args.command == "task-run":
        run_task_action(args)


def resolve_config(args: argparse.Namespace) -> None:
    client = _client_payload()
    if args.family == "tasks":
        outputs = _resolve_tasks(args, client)
    elif args.family == "release":
        outputs = _resolve_release(args, client)
    else:
        outputs = _resolve_job_family(args, client)
    _write_outputs(outputs)


def run_docker_job(args: argparse.Namespace) -> None:
    job = _load_job(args.job_json)
    jid = str(job["id"])
    if job.get("workflow_step") == "pages_deploy":
        print(f"::notice title={jid}::handled by upstream artifact job")
        return

    dockerfile = args.pipeline_src / str(job.get("dockerfile") or "")
    if not dockerfile.is_file():
        raise SystemExit(f"missing dockerfile for {jid}: {dockerfile}")
    target = str(job.get("target") or "")
    if not target:
        raise SystemExit(f"job {jid} missing target")

    tag = f"{args.tag_prefix}-{jid}"
    cmd = [
        "docker",
        "buildx",
        "build",
        "--load",
        "-f",
        str(dockerfile),
        "--target",
        target,
        "-t",
        tag,
    ]
    dockerignore = str(job.get("dockerignore") or "")
    ignore_backup: Path | None = None
    ignore_dst: Path | None = None
    if dockerignore:
        ignore_src = args.pipeline_src / dockerignore
        if ignore_src.is_file():
            ignore_dst = args.app_src / ".dockerignore"
            if ignore_dst.is_file():
                ignore_backup = args.app_src / ".dockerignore.pipeline-backup"
                shutil.copy(ignore_dst, ignore_backup)
            shutil.copy(ignore_src, ignore_dst)

    for key, value in _build_args(job, args.release_version).items():
        cmd.extend(["--build-arg", f"{key}={value}"])
    if target == "repo-hygiene" and job.get("hygiene_policy"):
        policy_json = json.dumps(job["hygiene_policy"], separators=(",", ":"))
        cmd.extend(["--build-arg", f"HYGIENE_POLICY_JSON={policy_json}"])

    cmd.append(str(args.app_src))
    print("==>", " ".join(shlex.quote(part) for part in cmd))
    try:
        subprocess.run(cmd, check=True)
    finally:
        if ignore_dst is not None and ignore_dst.is_file():
            if ignore_backup and ignore_backup.is_file():
                shutil.copy(ignore_backup, ignore_dst)
                ignore_backup.unlink()
            else:
                ignore_dst.unlink()
        if ignore_backup and ignore_backup.is_file():
            ignore_backup.unlink()
    _append_summary(job, target, dockerfile)

    if job.get("docker_socket"):
        subprocess.run(
            ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", tag],
            check=True,
        )
    if jid == "latex":
        _copy_pages_artifact(tag, args.pages_output)


def run_task_action(args: argparse.Namespace) -> None:
    command = ["cli", *_json_list(args.command_json)]
    env = os.environ.copy()
    for name, secret_name in _json_dict(args.env_json).items():
        env[name] = os.environ.get(secret_name, "")
    cwd = args.repo_dir if command[1:3] == ["tasks", "ingest-pr"] else None
    print("==>", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)
    _append_task_summary(command, cwd)


def _client_payload() -> dict[str, Any]:
    raw = (os.environ.get("CLIENT") or "{}").strip()
    if raw in {"", "null", "None"}:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid client payload: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit("client payload must be an object")
    return data


def _first(*values: str | None) -> str:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"missing workflow config: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"workflow config must be a mapping: {path}")
    return data


def _write_outputs(outputs: dict[str, Any]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        print(json.dumps(outputs, indent=2, sort_keys=True))
        return
    with open(output_path, "a", encoding="utf-8") as f:
        for key, value in outputs.items():
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                rendered = json.dumps(value, separators=(",", ":"))
            else:
                rendered = str(value)
            f.write(f"{key}={rendered}\n")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _repo_slug(repository: str) -> str:
    return repository.rsplit("/", 1)[-1]


def _config_repo(cfg: dict[str, Any]) -> tuple[str, str]:
    repository = str(cfg.get("repository") or cfg.get("repo") or "")
    repo_slug = str(cfg.get("repo_slug") or (_repo_slug(repository) if repository else ""))
    if not repository:
        raise SystemExit("workflow config must declare repository or repo")
    if not repo_slug:
        raise SystemExit("workflow config must declare repo_slug or a repo with owner/name")
    if cfg.get("repo") and cfg.get("repository") and cfg["repo"] != cfg["repository"]:
        raise SystemExit("workflow config has conflicting repo and repository values")
    if cfg.get("repo_slug") and _repo_slug(repository) != cfg["repo_slug"]:
        raise SystemExit("workflow config repo_slug does not match repository")
    return repo_slug, repository


def _validate_repo(cfg: dict[str, Any], requested_slug: str, requested_repository: str) -> tuple[str, str]:
    config_slug, config_repository = _config_repo(cfg)
    if requested_slug and requested_slug != config_slug:
        raise SystemExit(f"repo_slug {requested_slug!r} does not match config {config_slug!r}")
    if requested_repository and requested_repository != config_repository:
        raise SystemExit(f"repository {requested_repository!r} does not match config {config_repository!r}")
    return config_slug, config_repository


def _as_path(value: Any) -> Path | None:
    if value is None or value == "":
        return None
    if isinstance(value, Path):
        return value
    return Path(str(value))


def _apply_selective_jobs_if_configured(
    jobs: dict[str, dict[str, Any]],
    cfg: dict[str, Any],
    *,
    app_src: Path | None,
    selective_base: str,
    selective_head: str,
    force_full_suite: bool = False,
) -> dict[str, dict[str, Any]]:
    from src.services.pipeline_selective import apply_selective_jobs

    return apply_selective_jobs(
        jobs,
        cfg=cfg,
        app_src=app_src,
        selective_base=selective_base,
        selective_head=selective_head,
        force_full_suite=force_full_suite,
    )


def _stage_jobs(
    cfg: dict[str, Any],
    requested_job: str = "",
    *,
    app_src: Path | None = None,
    selective_base: str = "",
    selective_head: str = "",
    force_full_suite: bool = False,
) -> list[list[dict[str, Any]]]:
    raw_jobs = cfg.get("jobs") or []
    if not isinstance(raw_jobs, list):
        raise SystemExit("jobs must be a list")
    jobs: dict[str, dict[str, Any]] = {}
    for raw in raw_jobs:
        if not isinstance(raw, dict) or not raw.get("id"):
            raise SystemExit("each job must be a mapping with an id")
        jid = str(raw["id"])
        if jid in jobs:
            raise SystemExit(f"duplicate job id: {jid}")
        jobs[jid] = dict(raw)
    jobs = _apply_selective_jobs_if_configured(
        jobs,
        cfg,
        app_src=app_src,
        selective_base=selective_base,
        selective_head=selective_head,
        force_full_suite=force_full_suite,
    )
    if requested_job:
        if requested_job not in jobs:
            raise SystemExit(f"unknown job: {requested_job}")
        jobs = {requested_job: jobs[requested_job]}
    stages: list[list[dict[str, Any]]] = []
    completed: set[str] = set()
    remaining = dict(jobs)
    while remaining:
        current_ids = [
            jid
            for jid, job in remaining.items()
            if all(dep in completed or dep not in jobs for dep in _as_list(job.get("needs")))
        ]
        if not current_ids:
            raise SystemExit(f"cyclic or unsatisfied job dependencies: {sorted(remaining)}")
        stage: list[dict[str, Any]] = []
        for jid in current_ids:
            job = remaining.pop(jid)
            dockerfile = job.get("dockerfile") or cfg.get("dockerfile")
            dockerignore = job.get("dockerignore") or cfg.get("dockerignore") or ""
            if not dockerfile and not job.get("workflow_step"):
                raise SystemExit(f"job {jid} missing dockerfile")
            stage.append(
                {
                    "id": jid,
                    "name": job.get("name") or jid,
                    "target": job.get("target") or "",
                    "dockerfile": dockerfile or "",
                    "dockerignore": dockerignore,
                    "docker_socket": bool(job.get("docker_socket")),
                    "workflow_step": job.get("workflow_step") or "",
                    "build_args": job.get("build_args") or {},
                    "build_args_from_ref": bool(job.get("build_args_from_ref")),
                    "secrets": job.get("secrets") or {},
                    "hygiene_policy": job.get("hygiene_policy") or {},
                }
            )
        stages.append(stage)
        completed.update(current_ids)
        if len(stages) > MAX_STAGES:
            raise SystemExit(f"workflow has more than {MAX_STAGES} dependency stages")
    return stages


def _matrix(stage: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {"include": [{"job": job} for job in stage]}


def _stage_outputs(stages: list[list[dict[str, Any]]]) -> dict[str, Any]:
    outputs: dict[str, Any] = {"stage_count": len(stages)}
    for idx in range(MAX_STAGES):
        stage = stages[idx] if idx < len(stages) else []
        outputs[f"has_stage_{idx}"] = bool(stage)
        outputs[f"stage_{idx}"] = _matrix(stage)
    return outputs


def _config_path(pipeline_src: Path, family: str, repo_slug: str, pipeline: str) -> Path:
    base = pipeline_src / ".github" / "workflows" / family
    if family == "pull-request" and pipeline:
        flat = base / f"{repo_slug}-{pipeline}.yaml"
        if flat.is_file():
            return flat
        return base / repo_slug / f"{pipeline}.yaml"
    return base / f"{repo_slug}.yaml"


def _resolve_job_family(args: argparse.Namespace, client: dict[str, Any]) -> dict[str, Any]:
    repo_slug = _first(client.get("repo_slug"), args.repo_slug)
    pipeline = _first(client.get("pipeline"), args.pipeline)
    repository = _first(client.get("repository"), args.repository)
    ref = _first(
        client.get("ref"),
        (client.get("pull_request") or {}).get("head", {}).get("ref")
        if isinstance(client.get("pull_request"), dict)
        else "",
        args.ref,
    )
    sha = _first(client.get("sha"), args.sha)
    checkout_ref = sha or ref
    requested_job = _first(client.get("job"), args.job)
    if not repo_slug:
        raise SystemExit("repo_slug is required")
    if not checkout_ref:
        raise SystemExit("ref or sha is required")
    config = _config_path(args.pipeline_src, args.family, repo_slug, pipeline)
    cfg = _load_yaml(config)
    config_slug, config_repository = _validate_repo(cfg, repo_slug, repository)
    stages = _stage_jobs(
        cfg,
        requested_job=requested_job,
        app_src=_as_path(getattr(args, "app_src", None)),
        selective_base=str(getattr(args, "selective_base", "") or ""),
        selective_head=str(getattr(args, "selective_head", "") or ""),
        force_full_suite=bool(getattr(args, "force_full_suite", False)),
    )
    outputs: dict[str, Any] = {
        "repo_slug": config_slug,
        "repository": config_repository,
        "ref": ref,
        "sha": sha,
        "checkout_ref": checkout_ref,
        "pipeline": pipeline,
        "job": requested_job,
        "config": str(config),
        "pages_enabled": any(job.get("workflow_step") == "pages_deploy" for stage in stages for job in stage),
    }
    outputs.update(_stage_outputs(stages))
    return outputs


def _resolve_release(args: argparse.Namespace, client: dict[str, Any]) -> dict[str, Any]:
    repo_slug = _first(client.get("repo_slug"), args.repo_slug)
    repository = _first(client.get("repository"), args.repository)
    ref = _first(client.get("ref"), args.ref)
    if not repo_slug or not repository or not ref:
        raise SystemExit("repo_slug, repository, and ref are required")
    version = ref.removeprefix("refs/tags/").removeprefix("v")
    config = _config_path(args.pipeline_src, "release", repo_slug, "")
    cfg = _load_yaml(config)
    config_slug, config_repository = _validate_repo(cfg, repo_slug, repository)
    stages = _stage_jobs(cfg)
    outputs: dict[str, Any] = {
        "repo_slug": config_slug,
        "repository": config_repository,
        "ref": ref,
        "checkout_ref": ref,
        "config": str(config),
        "version": version,
        "pages_enabled": False,
    }
    outputs.update(_stage_outputs(stages))
    return outputs


def _resolve_tasks(args: argparse.Namespace, client: dict[str, Any]) -> dict[str, Any]:
    repo_slug = _first(client.get("repo_slug"), args.repo_slug)
    action = _first(client.get("action"), args.action)
    repository = _first(client.get("repository"), args.repository)
    ref = _first(client.get("ref"), args.ref, "main")
    dry_run = str(_first(str(client.get("dry_run")) if "dry_run" in client else "", args.dry_run, "true")).lower()
    if dry_run in {"1", "yes"}:
        dry_run = "true"
    if dry_run in {"0", "no"}:
        dry_run = "false"
    if not repo_slug:
        raise SystemExit("repo_slug is required")
    if not action:
        raise SystemExit("action is required")
    config = _config_path(args.pipeline_src, "tasks", repo_slug, "")
    cfg = _load_yaml(config)
    config_slug, config_repository = _validate_repo(cfg, repo_slug, repository)
    actions = cfg.get("actions") or {}
    if action not in actions:
        raise SystemExit(f"unknown action: {action}")
    action_cfg = actions[action] or {}
    command = list(action_cfg.get("cli") or [])
    if not command:
        raise SystemExit(f"task action {action} missing cli command")
    if dry_run == "true" and action in {"github-deploy", "github-prune-closed"}:
        command.append("--dry-run")
    env_map = action_cfg.get("env") or {}
    secrets = list(action_cfg.get("secrets") or [])
    preflight = action != "github-prune-closed"
    return {
        "repo_slug": config_slug,
        "repository": config_repository,
        "ref": ref,
        "action": action,
        "config": str(config),
        "dry_run": dry_run,
        "preflight": preflight,
        "task_command": json.dumps(command, separators=(",", ":")),
        "task_env": json.dumps(env_map, separators=(",", ":")),
        "task_secrets": json.dumps(secrets, separators=(",", ":")),
    }


def _load_job(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid job JSON: {exc}") from exc
    if "job" in data and isinstance(data["job"], dict):
        data = data["job"]
    if not isinstance(data, dict) or not data.get("id"):
        raise SystemExit("job JSON must be an object with an id")
    return data


def _build_args(job: dict[str, Any], release_version: str) -> dict[str, str]:
    args = {str(k): str(v) for k, v in (job.get("build_args") or {}).items()}
    if job.get("build_args_from_ref"):
        args["CLI_RELEASE_VERSION"] = release_version
    for arg, secret_name in (job.get("secrets") or {}).items():
        args[str(arg)] = os.environ.get(str(secret_name), "")
    return args


def _copy_pages_artifact(tag: str, output_dir: Path) -> None:
    container = "resume-pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["docker", "rm", "-f", container], check=False, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "create", "--name", container, tag], check=True)
    try:
        subprocess.run(["docker", "cp", f"{container}:/workspace/resume.pdf", str(output_dir)], check=True)
    finally:
        subprocess.run(["docker", "rm", container], check=False, stdout=subprocess.DEVNULL)


def _append_summary(job: dict[str, Any], target: str, dockerfile: Path) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("### Docker job\n\n")
        f.write(f"- Job: `{job['id']}`\n")
        f.write(f"- Target: `{target}`\n")
        f.write(f"- Dockerfile: `{dockerfile}`\n")


def _json_list(raw: str) -> list[str]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("task command must be a JSON list")
    return [str(item) for item in data]


def _json_dict(raw: str) -> dict[str, str]:
    data = json.loads(raw or "{}")
    if not isinstance(data, dict):
        raise SystemExit("task env must be a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def _append_task_summary(command: list[str], cwd: Path | None) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("### Task action\n\n")
        f.write(f"- Command: `{' '.join(command)}`\n")
        if cwd is not None:
            f.write(f"- Working directory: `{cwd}`\n")


if __name__ == "__main__":
    main()
