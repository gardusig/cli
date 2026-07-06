"""CLI tests for project pairs deploy partial failure."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_project_deploy_exits_nonzero_on_partial_failure(monkeypatch) -> None:
    from src.commands import project

    svc = MagicMock()
    svc.default_ref.return_value = MagicMock()
    svc.snapshot_summary.return_value = ["owner: o", "project: 1"]
    svc.deploy_pairs.return_value = {
        "results": [{"name": "docs", "action": "created"}],
        "failed": [{"name": "broken", "error": "rate limited"}],
    }
    monkeypatch.setattr(project, "_svc", lambda repo=None: svc)

    result = runner.invoke(app, ["project", "deploy", "--yes"])

    assert result.exit_code == 1
    assert "failed broken" in result.stderr


def test_project_deploy_succeeds_when_no_failures(monkeypatch) -> None:
    from src.commands import project

    svc = MagicMock()
    svc.default_ref.return_value = MagicMock()
    svc.snapshot_summary.return_value = ["owner: o", "project: 1"]
    svc.deploy_pairs.return_value = {"results": [{"name": "docs", "action": "created"}], "failed": []}
    monkeypatch.setattr(project, "_svc", lambda repo=None: svc)

    result = runner.invoke(app, ["project", "deploy", "--yes"])

    assert result.exit_code == 0
