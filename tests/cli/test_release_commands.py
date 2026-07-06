from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@patch("src.commands.release_cmd.read_project_version", return_value="1.2.3")
@patch("src.commands.release_cmd.require_write_gate", side_effect=RuntimeError("blocked"))
def test_release_main_requires_write_gate(_gate: MagicMock, _version: MagicMock) -> None:
    result = runner.invoke(app, ["release", "main"])

    assert result.exit_code != 0


@patch("src.commands.release_cmd._ensure_github_release")
@patch("src.commands.release_cmd.verify_package_version_on_index")
@patch("src.commands.release_cmd.publish_distributions", return_value=["pkg.whl"])
@patch("src.commands.release_cmd.resolve_pypi_token", return_value="tok")
@patch("src.commands.release_cmd.build_distributions", return_value=[Path("dist/pkg.whl")])
@patch("src.commands.release_cmd._ensure_release_tag")
@patch("src.commands.release_cmd.require_write_gate")
def test_release_main_publishes_and_verifies(
    mock_gate: MagicMock,
    mock_tag: MagicMock,
    mock_build: MagicMock,
    _token: MagicMock,
    mock_publish: MagicMock,
    mock_verify: MagicMock,
    mock_release: MagicMock,
) -> None:
    result = runner.invoke(app, ["release", "main", "--yes", "--version", "1.2.3"])

    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    assert "Released gardusig-cli==1.2.3" in result.stdout
    mock_gate.assert_called_once()
    mock_tag.assert_called_once_with("v1.2.3")
    _, build_kwargs = mock_build.call_args
    assert build_kwargs["version"] == "1.2.3"
    mock_publish.assert_called_once()
    mock_verify.assert_called_once_with("gardusig-cli", "1.2.3")
    mock_release.assert_called_once_with("v1.2.3")


def test_release_main_invalid_version_reports_error() -> None:
    result = runner.invoke(app, ["release", "main", "--yes", "--version", "bad"])

    assert result.exit_code != 0
    assert "release version must look like semver" in result.stdout + (result.stderr or "")
