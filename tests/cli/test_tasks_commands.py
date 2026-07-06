"""cli tasks shortcuts and ingest-pr dispatcher."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_tasks_list_json() -> None:
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0
    assert "notion" in result.stdout
    assert "github" in result.stdout


def test_tasks_run_notion_ingest(monkeypatch) -> None:
    called = MagicMock()
    monkeypatch.setattr("src.commands.notion.ingest_cmd", called)
    result = runner.invoke(app, ["tasks", "run", "notion", "ingest"])
    assert result.exit_code == 0
    called.assert_called_once_with()


def test_tasks_run_notion_deploy(monkeypatch) -> None:
    called = MagicMock()
    monkeypatch.setattr("src.commands.notion.deploy_cmd", called)
    result = runner.invoke(app, ["tasks", "run", "notion", "deploy", "--yes"])
    assert result.exit_code == 0
    called.assert_called_once_with(yes=True, cleanup=None)


def test_tasks_run_unknown_op() -> None:
    result = runner.invoke(app, ["tasks", "run", "notion", "prune"])
    assert result.exit_code != 0
    assert "Unknown task operation" in result.stdout + result.stderr


def test_tasks_ingest_pr_notion(monkeypatch) -> None:
    export = MagicMock()
    build = MagicMock()
    validate = MagicMock()
    gate = MagicMock()
    monkeypatch.setattr("src.commands.tasks.require_write_gate", gate)
    monkeypatch.setattr("src.commands.tasks.export_tasks", export)
    monkeypatch.setattr("src.commands.tasks.pairs_build_cmd", build)
    monkeypatch.setattr("src.commands.tasks.pairs_validate_cmd", validate)
    monkeypatch.setattr("src.commands.tasks.require_notion_token", lambda cfg: "tok")
    monkeypatch.setattr("src.commands.tasks.load_config", lambda: MagicMock(notion=MagicMock()))
    monkeypatch.setattr(
        "src.commands.tasks.subprocess.run",
        lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
    )
    result = runner.invoke(app, ["tasks", "ingest-pr", "--source", "notion", "--yes"])
    assert result.exit_code == 0
    gate.assert_called_once()
    export.assert_called_once()
    build.assert_called_once()
    validate.assert_called_once_with(format="json")
