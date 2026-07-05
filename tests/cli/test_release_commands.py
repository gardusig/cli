from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@patch("src.commands.release_cmd.read_project_version", return_value="1.2.3")
@patch("src.commands.release_cmd.require_write_gate", side_effect=RuntimeError("blocked"))
def test_release_main_requires_write_gate(_gate: MagicMock, _version: MagicMock) -> None:
    result = runner.invoke(app, ["release", "main"])

    assert result.exit_code != 0
