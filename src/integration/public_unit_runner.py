"""Run public CLI operation checks in unit tests (mocked externals, no docker guard)."""

from __future__ import annotations

from pathlib import Path

from src.integration.contest_integration import execute_contest_integration_check
from src.integration.docker_integration import execute_docker_integration_check
from src.integration.git_mocks import patch_remote_git
from src.integration.public_commands import assert_public_command_registry_complete
from src.integration.public_endpoints import (
    EndpointCheck,
    execute_endpoint_integration_check,
    prepare_git_repo,
)


def assert_public_unit_registry_complete() -> None:
    """Every public command path must have a mocked unit-test check."""
    assert_public_command_registry_complete()


def run_unit_endpoint_check(
    check: EndpointCheck,
    *,
    repo_root: Path,
    git_root: Path,
    outside_git_root: Path,
) -> list[str]:
    with patch_remote_git():
        return execute_endpoint_integration_check(
            check,
            repo_root=repo_root,
            git_root=git_root,
            outside_git_root=outside_git_root,
        )


def prepare_unit_git_roots(tmp_path: Path) -> tuple[Path, Path]:
    git_root = tmp_path / "git-root"
    prepare_git_repo(git_root)
    outside = tmp_path / "outside-git"
    outside.mkdir()
    return git_root, outside


def run_unit_docker_check(check, *, repo_root: Path) -> list[str]:
    return execute_docker_integration_check(check, repo_root=repo_root)


def run_unit_contest_check(check, *, repo_root: Path) -> list[str]:
    return execute_contest_integration_check(check, repo_root=repo_root)
