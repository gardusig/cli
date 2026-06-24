"""Integration coverage for every public cli CLI endpoint."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest

from src.integration.docker_guard import (
    cleanup_integration_temp_dir,
    integration_temp_dir,
)
from src.integration.public_endpoints import (
    GIT_SUBCOMMANDS,
    TOP_LEVEL_COMMANDS,
    assert_every_git_subcommand_checked,
    assert_every_git_subcommand_has_ok_and_failure_check,
    assert_every_top_level_command_checked,
    assert_registry_covers_git_commands,
    endpoint_checks,
    git_subcommands_covered_by_checks,
    git_subcommands_with_ok_check,
    git_subcommands_with_failure_check,
    prepare_git_repo,
    registered_git_subcommands,
    run_all_endpoint_checks,
)


def test_registry_matches_registered_git_commands() -> None:
    assert_registry_covers_git_commands()
    assert registered_git_subcommands() == set(GIT_SUBCOMMANDS)


def test_every_git_subcommand_has_integration_check() -> None:
    assert_every_git_subcommand_checked()
    assert git_subcommands_covered_by_checks() == set(GIT_SUBCOMMANDS)


def test_every_git_subcommand_has_ok_integration_check() -> None:
    assert git_subcommands_with_ok_check() == set(GIT_SUBCOMMANDS)


def test_every_git_subcommand_has_failure_integration_check() -> None:
    missing = set(GIT_SUBCOMMANDS) - git_subcommands_with_failure_check() - {"docs"}
    assert missing == set(), f"missing failure checks: {sorted(missing)}"


def test_top_level_commands_listed_in_registry() -> None:
    assert_every_top_level_command_checked()
    for name in TOP_LEVEL_COMMANDS:
        if name == "git":
            continue
        assert any(c.args and c.args[0] == name for c in endpoint_checks())


def test_docker_top_level_in_registry() -> None:
    assert "docker" in TOP_LEVEL_COMMANDS
    assert any(c.label == "docker --help" for c in endpoint_checks())


@pytest.mark.integration
def test_run_all_public_endpoint_checks() -> None:
    git_dir = integration_temp_dir("cli-git-")
    try:
        prepare_git_repo(git_dir)
        errors = run_all_endpoint_checks(ROOT, git_root=git_dir)
    finally:
        cleanup_integration_temp_dir(git_dir)
    assert errors == [], "\n---\n".join(errors)
