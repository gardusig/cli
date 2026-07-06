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
def test_dispatch_repository_event_posts(mock_run: MagicMock) -> None:
    dispatch_repository_event(
        "pull-request",
        {"repo_slug": "python-cli", "repository": "gardusig/python-cli", "ref": "main"},
    )
    mock_run.assert_called_once()
    body = mock_run.call_args.kwargs["input"]
    payload = json.loads(body)
    assert payload["event_type"] == "pull-request"
    assert payload["client_payload"]["repo_slug"] == "python-cli"
