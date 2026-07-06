from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_lint_repo_dispatches(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr("src.commands._toolkit.run_cli_command", lambda *args, **kwargs: calls.append((args, kwargs)) or 0)
    result = runner.invoke(app, ["lint", "repo", "."])
    assert result.exit_code == 0
    assert calls[0][0][:3] == ("lint", "repo", Path("."))


def test_structure_check_dispatches_policy_options(monkeypatch, tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("allowed_extensions: [.md]\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr("src.commands._toolkit.run_cli_command", lambda *args, **kwargs: calls.append((args, kwargs)) or 0)
    result = runner.invoke(app, ["structure", "check", str(tmp_path), "--require-structure", "--policy-file", str(policy)])
    assert result.exit_code == 0
    assert calls[0][0][:3] == ("structure", "check", tmp_path)
    assert calls[0][1]["extra_env"]["REQUIRE_STRUCTURE"] == "1"


def test_validate_vault_dispatches_base(monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("src.commands._toolkit.run_cli_command", lambda *args, **kwargs: calls.append((args, kwargs)) or 0)
    result = runner.invoke(app, ["validate", "vault", str(tmp_path), "--base", "origin/main"])
    assert result.exit_code == 0
    assert calls[0][0][:3] == ("validate", "vault", tmp_path)
    assert calls[0][1]["extra_env"]["BASE"] == "origin/main"


def test_test_python_unit_dispatches_suite(monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("src.commands._toolkit.run_cli_command", lambda *args, **kwargs: calls.append((args, kwargs)) or 0)
    result = runner.invoke(app, ["test", "python", "unit", str(tmp_path)])
    assert result.exit_code == 0
    assert calls[0][0][:3] == ("test", "python", tmp_path)
    assert calls[0][1]["suite"] == "unit"

