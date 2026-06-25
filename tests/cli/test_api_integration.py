"""One integration test per public API-backed CLI command (ok + fail)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.integration.cli_api_checks import CliApiCheck, cli_api_checks
from src.integration.workspaces import fixture_dir
from tests.harness.cli_api_harness import GH_WS, run_cli_api_checks

RUNNER = CliRunner()


def _api_checks(tmp_path: Path) -> list[CliApiCheck]:
    return cli_api_checks(gh_workspace=fixture_dir(GH_WS), drive_repo=str(tmp_path / "r"))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "cli_api_check" not in metafunc.fixturenames:
        return
    checks = _api_checks(Path("/tmp/cli-api-parametrize"))
    metafunc.parametrize(
        "cli_api_check",
        checks,
        ids=[check.label for check in checks],
    )


def test_cli_api_registry_has_ok_and_fail_per_command(tmp_path: Path) -> None:
    from src.integration.cli_api_checks import assert_every_api_command_has_ok_and_fail_check

    assert_every_api_command_has_ok_and_fail_check(_api_checks(tmp_path))


@pytest.mark.integration
def test_cli_api_command(
    cli_api_check: CliApiCheck,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors = run_cli_api_checks(
        [cli_api_check],
        RUNNER,
        monkeypatch,
        tmp_path,
        gh_workspace=fixture_dir(GH_WS),
    )
    assert errors == [], "\n---\n".join(errors)
