"""Every public CLI command must pass dockerized integration (registry + execution)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest

from src.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
from src.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    docker_subcommands_with_failure_check,
    docker_subcommands_with_ok_check,
)
from src.integration.public_commands import (
    assert_public_command_registry_complete,
    registered_top_level_commands,
    run_all_public_command_checks,
)
from src.integration.public_endpoints import (
    GIT_SUBCOMMANDS,
    PYPI_SUBCOMMANDS,
    TOP_LEVEL_COMMANDS,
    git_subcommands_with_ok_check,
    git_subcommands_with_failure_check,
    pypi_subcommands_with_ok_check,
    pypi_subcommands_with_failure_check,
    prepare_git_repo,
)
from src.services.test_packages import assert_registry_covers_top_level_commands


def test_top_level_commands_match_cli_registration() -> None:
    assert registered_top_level_commands() == set(TOP_LEVEL_COMMANDS)
    assert_registry_covers_top_level_commands()


def test_public_command_registry_is_complete() -> None:
    from src.integration.integration_coverage import assert_integration_coverage_gate

    assert_integration_coverage_gate()
    assert git_subcommands_with_ok_check() == set(GIT_SUBCOMMANDS)
    missing_git_fail = set(GIT_SUBCOMMANDS) - git_subcommands_with_failure_check() - {"docs"}
    assert missing_git_fail == set()
    assert pypi_subcommands_with_ok_check() == set(PYPI_SUBCOMMANDS)
    assert pypi_subcommands_with_failure_check() == set(PYPI_SUBCOMMANDS)
    assert docker_subcommands_with_ok_check() == set(DOCKER_SUBCOMMANDS)
    assert docker_subcommands_with_failure_check() == set(DOCKER_SUBCOMMANDS)


def test_docker_harness_includes_public_command_checker() -> None:
    path = ROOT / "tests" / "integration" / "check_public_commands.py"
    assert path.is_file() and path.stat().st_size > 0


@pytest.mark.integration
def test_all_public_commands_in_dockerized_integration() -> None:
    git_dir = integration_temp_dir("cli-public-")
    try:
        prepare_git_repo(git_dir)
        errors = run_all_public_command_checks(ROOT, git_root=git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    assert errors == [], "\n---\n".join(errors)
