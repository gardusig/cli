"""Parametrized unit tests for notion/drive/chrome CLI operations (APIs mocked)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from src.integration.cli_api_checks import cli_api_checks
from tests.harness.cli_api_harness import run_cli_api_check

runner = CliRunner()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "api_check" in metafunc.fixturenames:
        checks = cli_api_checks(drive_repo=".")
        metafunc.parametrize("api_check", checks, ids=[check.label for check in checks])


def test_public_api_operation(api_check, monkeypatch, tmp_path) -> None:
    err = run_cli_api_check(runner, api_check, monkeypatch, tmp_path)
    assert err is None, err
