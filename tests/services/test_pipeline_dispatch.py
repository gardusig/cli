"""Tests for hub pipeline repository_dispatch."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.services.pipeline_dispatch import dispatch_repository_event


def test_dispatch_repository_event_dry_run() -> None:
    result = dispatch_repository_event(
        "operator",
        {"lane": "test", "repository": "gardusig/python-cli", "ref": "main"},
        dry_run=True,
    )
    assert result["event_type"] == "operator"
    assert result["client_payload"]["lane"] == "test"


@patch("src.services.pipeline_dispatch.subprocess.run")
@patch("src.services.pipeline_dispatch.list_active_hub_runs", return_value=[])
def test_dispatch_repository_event_posts(mock_active: MagicMock, mock_run: MagicMock) -> None:
    dispatch_repository_event(
        "pull-request",
        {"repo_slug": "python-cli", "repository": "gardusig/python-cli", "ref": "main"},
    )
    mock_active.assert_called_once()
    mock_run.assert_called_once()


@patch("src.services.pipeline_dispatch.list_active_hub_runs", return_value=[{"databaseId": 1, "url": "https://example/run/1"}])
def test_dispatch_repository_event_skips_when_hub_run_active(mock_active: MagicMock) -> None:
    import pytest

    with pytest.raises(SystemExit, match="active pull-request run"):
        dispatch_repository_event(
            "pull-request",
            {"repo_slug": "python-cli", "repository": "gardusig/cli", "ref": "main"},
        )
    mock_active.assert_called_once()


@patch("src.services.pipeline_dispatch.subprocess.run")
@patch("src.services.pipeline_dispatch.list_active_hub_runs", return_value=[{"databaseId": 1}])
def test_dispatch_repository_event_force_bypasses_active_guard(
    mock_active: MagicMock,
    mock_run: MagicMock,
) -> None:
    dispatch_repository_event(
        "pull-request",
        {"repo_slug": "python-cli", "repository": "gardusig/cli", "ref": "main"},
        force=True,
    )
    mock_active.assert_not_called()
    mock_run.assert_called_once()
