"""PyPI CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.cli import app

runner = CliRunner()


@patch("cli.commands.pypi.build_distributions")
def test_pypi_build(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/gardusig_cli-1.0.0-py3-none-any.whl")]
    result = runner.invoke(app, ["pypi", "build", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
    _, kwargs = mock_build.call_args
    assert kwargs["version"] == "1.0.0"


@patch("cli.commands.pypi.publish_distributions")
@patch("cli.commands.pypi.build_distributions")
@patch("cli.commands.pypi.resolve_pypi_token", return_value="tok")
@patch("cli.commands.pypi.require_write_gate")
def test_pypi_upload(
    _gate: MagicMock,
    _token: MagicMock,
    mock_build: MagicMock,
    mock_upload: MagicMock,
) -> None:
    mock_build.return_value = [Path("dist/pkg.whl")]
    mock_upload.return_value = ["pkg.whl"]
    result = runner.invoke(app, ["pypi", "upload", "--yes", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Published to PyPI" in result.stdout


@patch("cli.commands.pypi.build_distributions")
def test_publish_pypi_build_only_deprecated(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/gardusig_cli-0.1.0-py3-none-any.whl")]
    result = runner.invoke(app, ["publish", "pypi", "--build-only"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
