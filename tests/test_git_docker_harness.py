"""Unit-level assertions for git/docker integration harness completeness."""

from __future__ import annotations

from shuttle.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    assert_docker_registry_covers_commands,
    assert_every_docker_subcommand_has_ok_and_failure_check,
    docker_checks,
    registered_docker_subcommands,
)
from shuttle.integration.public_endpoints import (
    GIT_SUBCOMMANDS,
    assert_every_git_subcommand_checked,
    assert_every_git_subcommand_has_ok_and_failure_check,
    assert_registry_covers_git_commands,
    endpoint_checks,
    registered_git_subcommands,
)


def test_git_registry_matches_cli() -> None:
    assert_registry_covers_git_commands()
    assert registered_git_subcommands() == set(GIT_SUBCOMMANDS)


def test_every_git_subcommand_has_ok_and_failure_coverage() -> None:
    assert_every_git_subcommand_checked()
    assert_every_git_subcommand_has_ok_and_failure_check()


def test_docker_registry_matches_cli() -> None:
    assert_docker_registry_covers_commands()
    assert registered_docker_subcommands() == set(DOCKER_SUBCOMMANDS)


def test_every_docker_subcommand_has_ok_and_failure_integration_check() -> None:
    assert_every_docker_subcommand_has_ok_and_failure_check()


def test_git_endpoint_count() -> None:
    git_checks = [c for c in endpoint_checks() if c.args and c.args[0] == "git"]
    assert len(git_checks) >= len(GIT_SUBCOMMANDS) * 2


def test_docker_integration_check_count() -> None:
    assert len(docker_checks()) >= len(DOCKER_SUBCOMMANDS) * 2
