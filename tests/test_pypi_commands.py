"""PyPI CLI commands (mocked service layer — real build in test_pypi_integration)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gardusig_cli.cli import app

runner = CliRunner()


@patch("gardusig_cli.commands.pypi.build_distributions")
def test_pypi_build(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/gardusig_cli-1.0.0-py3-none-any.whl")]
    result = runner.invoke(app, ["pypi", "build", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
    _, kwargs = mock_build.call_args
    assert kwargs["version"] == "1.0.0"


@patch("gardusig_cli.commands.pypi.verify_package_version_on_index")
@patch("gardusig_cli.commands.pypi.publish_distributions")
@patch("gardusig_cli.commands.pypi.build_distributions")
@patch("gardusig_cli.commands.pypi.resolve_pypi_token", return_value="tok")
@patch("gardusig_cli.commands.pypi.require_write_gate")
def test_pypi_upload(
    _gate: MagicMock,
    _token: MagicMock,
    mock_build: MagicMock,
    mock_upload: MagicMock,
    _verify: MagicMock,
) -> None:
    mock_build.return_value = [Path("dist/pkg.whl")]
    mock_upload.return_value = ["pkg.whl"]
    result = runner.invoke(app, ["pypi", "upload", "--yes", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Published to PyPI" in result.stdout
    assert "Verified on PyPI" in result.stdout


@patch("gardusig_cli.commands.pypi.build_distributions")
def test_publish_pypi_build_only_deprecated(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/gardusig_cli-0.1.0-py3-none-any.whl")]
    result = runner.invoke(app, ["publish", "pypi", "--build-only"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
