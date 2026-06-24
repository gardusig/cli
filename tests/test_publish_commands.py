"""Publish CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.cli import app

runner = CliRunner()


@patch("cli.commands.publish.build_distributions")
def test_publish_pypi_build_only(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/gardusig_cli-0.1.0-py3-none-any.whl")]
    result = runner.invoke(app, ["publish", "pypi", "--build-only"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
    mock_build.assert_called_once()


@patch("cli.commands.publish.publish_distributions")
@patch("cli.commands.publish.build_distributions")
@patch("cli.commands.publish.resolve_pypi_token", return_value="tok")
@patch("cli.commands.publish.require_write_gate")
def test_publish_pypi_upload(
    _gate: MagicMock,
    _token: MagicMock,
    mock_build: MagicMock,
    mock_upload: MagicMock,
) -> None:
    mock_build.return_value = [Path("dist/pkg.whl")]
    mock_upload.return_value = ["pkg.whl"]
    result = runner.invoke(app, ["publish", "pypi", "--yes"])
    assert result.exit_code == 0
    assert "Published to PyPI" in result.stdout
