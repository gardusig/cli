from __future__ import annotations

import json

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_test_packages_resolve_outputs_json_contract() -> None:
    result = runner.invoke(
        app,
        ["test", "packages", "resolve", "--changed-path", "src/commands/git.py"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "git" in payload["package_names"]
    assert payload["requires_ai"] is False
    assert any(path.startswith("tests/git") for path in payload["unit_test_paths"])
    assert payload["pipeline_contract"]["owner"] == "gardusig/cli"


def test_test_packages_resolve_table_output() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "packages",
            "resolve",
            "--changed-path",
            "src/providers/opencode.py",
            "--format",
            "table",
        ],
    )

    assert result.exit_code == 0
    assert "packages: opencode" in result.stdout
    assert "paid AI commands" in result.stdout


def test_test_packages_resolve_rejects_unknown_format() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "packages",
            "resolve",
            "--changed-path",
            "src/commands/git.py",
            "--format",
            "yaml",
        ],
    )

    assert result.exit_code != 0
    assert "expected one of: json, table" in result.output


def test_test_packages_list_outputs_registry() -> None:
    result = runner.invoke(app, ["test", "packages", "list", "--format", "table"])

    assert result.exit_code == 0
    assert "git:" in result.stdout
    assert "tests/git/" in result.stdout


def test_test_packages_run_dry_run_outputs_commands() -> None:
    result = runner.invoke(
        app,
        ["test", "packages", "run", "git", "--dry-run", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["package"]["name"] == "git"
    assert any(command["kind"] == "unit" for command in payload["commands"])


def test_test_packages_run_can_emit_integration_only_commands() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "packages",
            "run",
            "git",
            "--no-unit",
            "--dry-run",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["commands"]
    assert {command["kind"] for command in payload["commands"]} == {"integration"}


def test_test_packages_suite_outputs_full_contract() -> None:
    result = runner.invoke(app, ["test", "packages", "suite", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "git" in payload["packages"]
    assert payload["pipeline_contract"]["owner"] == "gardusig/cli"


def test_test_packages_resolve_can_use_git_range(monkeypatch) -> None:
    from src.commands import test_cmd

    monkeypatch.setattr(
        test_cmd,
        "changed_paths_from_git",
        lambda base, head, repo_root: ["src/commands/git.py"],
    )

    result = runner.invoke(
        app,
        ["test", "packages", "resolve", "--base", "main", "--head", "HEAD"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["changed_paths"] == ["src/commands/git.py"]
    assert payload["package_names"] == ["git"]
