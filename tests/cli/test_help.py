from tests.constants import ROOT

from typer.testing import CliRunner

from src import __version__
from src.cli import app

runner = CliRunner()


def test_root_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "git" in result.stdout
    assert "docker" in result.stdout


def test_docker_help() -> None:
    result = runner.invoke(app, ["docker", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "ps",
        "stats",
        "containers",
        "images",
        "top",
        "df",
        "stop",
        "container-delete",
        "image-delete",
        "reset",
        "clean",
    ):
        assert cmd in result.stdout


def test_git_help() -> None:
    result = runner.invoke(app, ["git", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "commit",
        "push",
        "pull",
        "start",
        "main",
        "branch",
        "tag",
        "zip",
        "large",
        "review",
        "docs",
    ):
        assert cmd in result.stdout


def test_contest_validate_help() -> None:
    result = runner.invoke(app, ["contest", "validate", "--help"])
    assert result.exit_code == 0
    assert "--timeout" in result.stdout
    assert "--memory-mb" in result.stdout
    assert "--image" in result.stdout
    assert "--cxx-std" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
