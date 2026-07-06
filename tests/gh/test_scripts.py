"""Verify GitHub workflow commands remain cataloged after removing shell wrappers."""

from src.utils.catalog import GH_COMMANDS


def test_gh_workflow_commands_are_cataloged() -> None:
    commands = {command for _, command in GH_COMMANDS}
    assert "gh issue list" in commands
    assert "gh pr create" in commands
    assert "gh pr merge (blocked — policy)" in commands
