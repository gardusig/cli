"""HTTP timeout defaults."""

from __future__ import annotations

from tests.constants import ROOT

import subprocess
from unittest.mock import MagicMock, patch

from src.providers.notion import NotionClient
from src.utils.config import NotionConfig
from src.utils.http import DEFAULT_HTTP_TIMEOUT_SECONDS, default_http_timeout
from src.utils.process import run_gh


def test_default_http_timeout_is_30_seconds() -> None:
    assert DEFAULT_HTTP_TIMEOUT_SECONDS == 30.0
    assert default_http_timeout() == 30.0


def test_notion_client_uses_global_http_timeout() -> None:
    with patch("src.providers.notion.httpx.Client") as mock_client:
        NotionClient("tok", config=NotionConfig(database_id="db"))
        mock_client.assert_called_once()
        assert mock_client.call_args.kwargs["timeout"] == 30.0


@patch("src.utils.process.subprocess.run")
def test_run_gh_uses_default_timeout(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(["gh"], 0, "", "")
    run_gh(["auth", "status"])
    assert mock_run.call_args.kwargs["timeout"] == 30.0
