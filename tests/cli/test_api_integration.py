"""Mocked CLI integration: every public gh/notion/drive/chrome command (ok + fail)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.integration.cli_api_checks import (
    assert_every_api_command_has_ok_and_fail_check,
    cli_api_checks,
)
from src.integration.workspaces import fixture_dir
from tests.harness.cli_api_harness import GH_WS, run_cli_api_checks


RUNNER = CliRunner()


def test_cli_api_registry_has_ok_and_fail_per_command(tmp_path: Path) -> None:
    checks = cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=str(tmp_path / "r"))
    assert_every_api_command_has_ok_and_fail_check(checks)


@pytest.mark.integration
def test_gh_cli_api_commands(tmp_path: Path, monkeypatch) -> None:
    checks = [c for c in cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=".") if c.api == "gh"]
    errors = run_cli_api_checks(
        checks,
        RUNNER,
        monkeypatch,
        tmp_path,
        gh_workspace=fixture_dir(GH_WS),
    )
    assert errors == [], "\n---\n".join(errors)


@pytest.mark.integration
def test_notion_cli_api_commands(tmp_path: Path, monkeypatch) -> None:
    checks = [c for c in cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=".") if c.api == "notion"]
    errors = run_cli_api_checks(
        checks,
        RUNNER,
        monkeypatch,
        tmp_path,
        gh_workspace=fixture_dir(GH_WS),
    )
    assert errors == [], "\n---\n".join(errors)


@pytest.mark.integration
def test_drive_cli_api_commands(tmp_path: Path, monkeypatch) -> None:
    checks = [c for c in cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=".") if c.api == "drive"]
    errors = run_cli_api_checks(
        checks,
        RUNNER,
        monkeypatch,
        tmp_path,
        gh_workspace=fixture_dir(GH_WS),
    )
    assert errors == [], "\n---\n".join(errors)


@pytest.mark.integration
def test_chrome_cli_api_commands(tmp_path: Path, monkeypatch) -> None:
    checks = [c for c in cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=".") if c.api == "chrome"]
    errors = run_cli_api_checks(
        checks,
        RUNNER,
        monkeypatch,
        tmp_path,
        gh_workspace=fixture_dir(GH_WS),
    )
    assert errors == [], "\n---\n".join(errors)
