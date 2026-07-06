from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.providers.gh_transport import GhApiTransport, GhAutoTransport, GhTransportError


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.content = b"{}" if data != {} else b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._data


class FakeClient:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    responses: list[Any] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def request(self, method: str, path: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, path, kwargs))
        return FakeResponse(self.responses.pop(0))


@pytest.fixture(autouse=True)
def reset_fake_client() -> None:
    FakeClient.calls = []
    FakeClient.responses = []


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_api_transport_lists_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = [
        [
            {"number": 1, "title": "issue"},
            {"number": 2, "pull_request": {"url": "https://example.test/pr/2"}},
        ]
    ]
    transport = GhApiTransport(repo="owner/repo")

    data = transport.run_json(["issue", "list", "--state", "open", "--limit", "10"])

    assert data == [{"number": 1, "title": "issue"}]
    assert FakeClient.calls[0][0:2] == ("GET", "/repos/owner/repo/issues")
    assert FakeClient.calls[0][2]["params"]["per_page"] == 10


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_api_transport_reopens_pr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = [{"number": 7, "state": "open"}]
    transport = GhApiTransport(repo="owner/repo")

    data = transport.run_json(["pr", "reopen", "7"])

    assert data["state"] == "open"
    assert FakeClient.calls[0][0:2] == ("PATCH", "/repos/owner/repo/pulls/7")
    assert FakeClient.calls[0][2]["json"] == {"state": "open"}


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
@patch("src.providers.gh_transport.GhCliTransport.is_authenticated", return_value=False)
def test_auto_transport_falls_back_to_api(
    mock_auth: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = [[{"number": 1}]]
    transport = GhAutoTransport(repo="owner/repo")

    assert transport.run_json(["issue", "list"]) == [{"number": 1}]
    mock_auth.assert_called_once()


@patch("src.providers.gh_transport.GhCliTransport.is_authenticated", return_value=False)
@patch("src.providers.gh_transport.github_token", return_value=None)
def test_auto_transport_requires_cli_or_token(
    mock_token: MagicMock,
    mock_auth: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    with pytest.raises(GhTransportError):
        GhAutoTransport(repo="owner/repo")
    mock_token.assert_called_once()
    mock_auth.assert_called_once()
