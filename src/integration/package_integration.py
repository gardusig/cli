"""Per-package integration runners for selective CI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

from src.integration.cli_api_checks import ApiName, CliApiCheck, cli_api_checks
from src.integration.workspaces import API_WORKSPACES, fixture_dir

ApiPackage = Literal["gh", "notion", "drive", "chrome"]
RunnerPackage = ApiPackage | Literal["git", "docker", "contest", "project", "pypi", "cli"]

_API_PACKAGES: frozenset[str] = frozenset({"gh", "notion", "drive", "chrome"})
_RUNNER_PACKAGES: frozenset[str] = frozenset(
    {"gh", "notion", "drive", "chrome", "git", "docker", "contest", "project", "pypi", "cli"}
)

_PACKAGE_PYTEST_MODULES: dict[str, tuple[str, ...]] = {
    "pypi": ("tests/pypi/test_integration.py",),
    "git": ("tests/workflows/test_workflow_e2e.py",),
}


def runner_packages() -> frozenset[str]:
    return _RUNNER_PACKAGES


def package_pytest_modules(package: str) -> tuple[str, ...]:
    """Pytest file paths for a package integration leg."""
    for workspace in API_WORKSPACES:
        if workspace.name == package:
            return (workspace.integration_module.replace(".", "/") + ".py",)
    return _PACKAGE_PYTEST_MODULES.get(package, ())


def run_package_integration(package: str, repo_root: Path) -> list[str]:
    """Run mocked integration legs for one CLI package."""
    if package not in _RUNNER_PACKAGES:
        return [f"unknown package integration runner: {package}"]

    errors: list[str] = []
    errors.extend(_run_pytest_modules(package, repo_root))
    if package in _API_PACKAGES:
        errors.extend(_run_api_cli_checks(package, repo_root))  # type: ignore[arg-type]
    elif package == "git":
        errors.extend(_run_git_endpoint_checks(repo_root))
        errors.extend(_run_workflow_checks(repo_root))
    elif package == "docker":
        from src.integration.docker_integration import run_all_docker_checks

        errors.extend(run_all_docker_checks(repo_root))
    elif package == "contest":
        from src.integration.contest_integration import run_all_contest_checks

        errors.extend(run_all_contest_checks(repo_root))
    elif package == "project":
        from src.integration.project_integration import run_all_project_checks

        errors.extend(run_all_project_checks(repo_root))
    elif package == "cli":
        errors.extend(_run_public_command_checks(repo_root))
    return errors


def _run_pytest_modules(package: str, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for module_path in package_pytest_modules(package):
        code = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-cov", module_path],
            cwd=repo_root,
            check=False,
        ).returncode
        if code != 0:
            errors.append(f"{package} pytest {module_path}: exit {code}")
    return errors


def _run_api_cli_checks(api: ApiPackage, repo_root: Path) -> list[str]:
    from typer.testing import CliRunner

    from tests.harness.cli_api_harness import GH_WS, run_cli_api_checks

    gh_workspace = fixture_dir(GH_WS)
    with tempfile.TemporaryDirectory(prefix="cli-api-package-") as tmp:
        drive_repo = Path(tmp) / "drive-repo"
        drive_repo.mkdir()
        checks = [check for check in cli_api_checks(gh_workspace=gh_workspace, drive_repo=str(drive_repo)) if check.api == api]
        if not checks:
            return [f"{api}: no API integration checks registered"]
        import pytest

        runner = CliRunner()
        monkeypatch = pytest.MonkeyPatch()
        try:
            return run_cli_api_checks(
                checks,
                runner,
                monkeypatch,
                Path(tmp),
                gh_workspace=gh_workspace,
            )
        finally:
            monkeypatch.undo()


def _run_git_endpoint_checks(repo_root: Path) -> list[str]:
    from src.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
    from src.integration.git_mocks import patch_remote_git
    from src.integration.public_endpoints import endpoint_checks, execute_endpoint_integration_check, prepare_git_repo

    git_checks = [check for check in endpoint_checks() if check.args and check.args[0] in {"git", "g"}]
    git_dir = integration_temp_dir("cli-package-git-")
    outside = integration_temp_dir("cli-package-outside-")
    errors: list[str] = []
    try:
        prepare_git_repo(git_dir)
        with patch_remote_git():
            for check in git_checks:
                errors.extend(
                    execute_endpoint_integration_check(
                        check,
                        repo_root=repo_root,
                        git_root=git_dir,
                        outside_git_root=outside,
                    )
                )
    finally:
        cleanup_integration_temp_dir(git_dir)
        cleanup_integration_temp_dir(outside)
    return errors


def _run_workflow_checks(repo_root: Path) -> list[str]:
    from src.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
    from src.integration.workflow_integration import prepare_workflow_git, run_all_workflow_checks

    git_dir = integration_temp_dir("cli-package-workflow-")
    try:
        prepare_workflow_git(git_dir)
        return run_all_workflow_checks(repo_root, git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)


def _run_public_command_checks(repo_root: Path) -> list[str]:
    from src.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
    from src.integration.public_commands import run_all_public_command_checks
    from src.integration.public_endpoints import prepare_git_repo

    git_dir = integration_temp_dir("cli-package-public-")
    try:
        prepare_git_repo(git_dir)
        return run_all_public_command_checks(repo_root, git_root=git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)


def filtered_api_checks(checks: list[CliApiCheck], api: ApiName) -> list[CliApiCheck]:
    return [check for check in checks if check.api == api]
