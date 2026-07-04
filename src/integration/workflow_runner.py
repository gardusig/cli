"""Shared helpers for multi-step workflow integration tests."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.integration.docker_guard import integration_scratch_dir
from src.integration.git_mocks import patch_remote_git
from src.integration.public_endpoints import _push_cwd
from src.utils.config import project_root

_CLI_RUNNER = CliRunner()

WorkflowCheckFn = Callable[[Path, Path], list[str]]


@dataclass(frozen=True)
class WorkflowStep:
    """One CLI invocation in a workflow chain."""

    args: tuple[str, ...]
    needle: str
    exit_ok: int = 0


def workflow_scratch(name: str) -> Path:
    path = integration_scratch_dir(require_docker=False) / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def isolated_workflow_env(scratch: Path, fixture_rel: str | None = None) -> dict[str, str]:
    """Fixture-only config dir under *scratch* (never host iCloud paths)."""
    cfg_dir = scratch / "cli-config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    root = project_root()
    if fixture_rel:
        fixture_cfg = root / "tests" / "fixtures" / "workflows" / fixture_rel / "config.yaml"
        if fixture_cfg.is_file():
            shutil.copy(fixture_cfg, cfg_dir / "config.yaml")
        else:
            _write_minimal_config(cfg_dir, scratch)
    else:
        ci_cfg = root / "config" / "ci" / "config.yaml"
        if ci_cfg.is_file():
            shutil.copy(ci_cfg, cfg_dir / "config.yaml")
        else:
            _write_minimal_config(cfg_dir, scratch)
    tags_dir = scratch / "git-tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    return {"CLI_CONFIG_DIR": str(cfg_dir)}


def _write_minimal_config(cfg_dir: Path, scratch: Path) -> None:
    tags_dir = scratch / "git-tags"
    (cfg_dir / "config.yaml").write_text(
        f"backup:\n  tags_dir: {tags_dir}\n  repositories: []\n",
        encoding="utf-8",
    )


@contextmanager
def _nullcontext() -> Iterator[None]:
    yield


@contextmanager
def workflow_invoke_context(
    repo_root: Path,
    git_root: Path | None,
    *,
    extra_env: dict[str, str] | None = None,
    mock_remote: bool = True,
) -> Iterator[None]:
    """CLI_GIT_ROOT + remote git mock."""
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if git_root is not None:
        env["CLI_GIT_ROOT"] = str(git_root)
    if extra_env:
        env.update(extra_env)
    os.environ.update(env)

    remote_ctx = patch_remote_git() if mock_remote else _nullcontext()

    with remote_ctx, _push_cwd(repo_root):
        yield


def invoke_workflow_cli(
    repo_root: Path,
    git_root: Path | None,
    cli_args: tuple[str, ...],
    *,
    extra_env: dict[str, str] | None = None,
    mock_remote: bool = True,
) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if git_root is not None:
        env["CLI_GIT_ROOT"] = str(git_root)
    if extra_env:
        env.update(extra_env)
    with workflow_invoke_context(
        repo_root,
        git_root,
        extra_env=extra_env,
        mock_remote=mock_remote,
    ):
        result = _CLI_RUNNER.invoke(app, list(cli_args), env=env)
    return result.exit_code, result.stdout + (result.stderr or "")


def run_workflow_steps(
    repo_root: Path,
    git_root: Path | None,
    steps: list[WorkflowStep],
    *,
    extra_env: dict[str, str] | None = None,
    mock_remote: bool = True,
) -> list[str]:
    """Run *steps* in order; return error strings (empty if all pass)."""
    errors: list[str] = []
    for step in steps:
        code, output = invoke_workflow_cli(
            repo_root,
            git_root,
            step.args,
            extra_env=extra_env,
            mock_remote=mock_remote,
        )
        if code != step.exit_ok:
            errors.append(f"{step.args}: exit {code} (expected {step.exit_ok})\n{output}")
            return errors
        if step.needle and step.needle not in output:
            errors.append(f"{step.args}: missing {step.needle!r}\n{output}")
    return errors
