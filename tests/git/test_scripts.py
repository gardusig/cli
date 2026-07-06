"""Verify git workflow commands remain cataloged after removing shell wrappers."""

from src.utils.catalog import GIT_COMMANDS


def test_git_workflow_commands_are_cataloged() -> None:
    commands = {command for _, command in GIT_COMMANDS}
    assert "git start" in commands
    assert "git push" in commands
    assert "git branch delete --merged" in commands
