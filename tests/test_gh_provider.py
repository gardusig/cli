"""Unit tests for GhProvider subprocess wrapper."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from cli.providers.gh import GhProvider


@patch("cli.providers.gh.run_gh")
def test_run_injects_repo_flag(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
    provider = GhProvider(repo="owner/repo")
    assert provider.run(["issue", "list"]) == "ok"
    mock_run.assert_called_once_with(["--repo", "owner/repo", "issue", "list"], check=True)


@patch("cli.providers.gh.run_gh")
def test_run_json_parses_payload(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(stdout='[{"number": 1}]\n', returncode=0)
    provider = GhProvider()
    data = provider.run_json(["issue", "list"])
    assert data == [{"number": 1}]


@patch("cli.providers.gh.run_gh")
def test_run_json_empty_stdout_returns_list(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    provider = GhProvider()
    assert provider.run_json(["issue", "list"]) == []


@patch("cli.providers.gh.run_gh")
def test_default_repo_reads_name_with_owner(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(
        stdout=json.dumps({"nameWithOwner": "owner/repo"}) + "\n",
        returncode=0,
    )
    provider = GhProvider()
    assert provider.default_repo() == "owner/repo"
