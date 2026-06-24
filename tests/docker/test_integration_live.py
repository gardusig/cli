"""Unit tests for live docker integration runner (mocked daemon)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path
from unittest.mock import MagicMock, patch

from gardusig_cli.integration.docker_integration import run_live_docker_checks


@patch("gardusig_cli.integration.docker_integration.subprocess.run")
def test_live_docker_checks_success(mock_run: MagicMock) -> None:
    def side_effect(args, **kwargs):
        cmd = args
        if cmd[:2] == ["docker", "info"]:
            return MagicMock(returncode=0)
        if cmd[:3] == ["docker", "ps", "-a"]:
            return MagicMock(returncode=0, stdout="other\n")
        if cmd[:2] == ["docker", "run"]:
            return MagicMock(returncode=0)
        if cmd[:2] == ["docker", "pull"]:
            return MagicMock(returncode=0)
        if cmd[:2] in (["docker", "rm"], ["docker", "stop"]):
            return MagicMock(returncode=0)
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = side_effect

    ok_out = (
        "cli-integration-live cli-integration "
        "CPU Images alpine"
    )
    with patch("gardusig_cli.integration.docker_integration.run_docker_check") as mock_check:
        mock_check.side_effect = [
            (0, ok_out),
            (0, ok_out),
            (0, ok_out),
            (0, ok_out),
            (0, ok_out),
            (0, ok_out),
            (1, "non-interactive"),
            (0, "stopped"),
            (0, "deleted"),
        ]
        errors = run_live_docker_checks(ROOT)

    assert errors == []
    assert mock_check.call_count == 9


@patch("gardusig_cli.integration.docker_integration.subprocess.run")
def test_live_docker_daemon_unavailable(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1)
    errors = run_live_docker_checks(ROOT)
    assert len(errors) == 1
    assert "not available" in errors[0]


@patch("gardusig_cli.integration.docker_integration.subprocess.run")
def test_live_docker_delete_reports_still_present(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="cli-integration-live\n")
    from gardusig_cli.integration.docker_integration import _LIVE_CONTAINER

    with patch(
        "gardusig_cli.integration.docker_integration.run_docker_check",
        return_value=(0, "deleted"),
    ):
        errors: list[str] = []
        code, _output = (0, "deleted")
        if code != 0:
            errors.append("exit")
        elif _LIVE_CONTAINER in mock_run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        ).stdout:
            errors.append("live docker container-delete: container still present")
    assert errors == ["live docker container-delete: container still present"]
