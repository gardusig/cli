from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.providers.gh_transport import GhApiTransport, GhAutoTransport, GhTransportError

# P0 issue/PR commands exercised on API transport (see docs/gh.md Transport parity).
PARITY_P0_API_COMMANDS: tuple[tuple[list[str], str], ...] = (
    (["issue", "list"], "GET"),
    (["issue", "view", "1"], "GET"),
    (["issue", "reopen", "1"], "PATCH"),
    (["pr", "list"], "GET"),
    (["pr", "checks", "7"], "GET"),
    (["pr", "review", "7", "--approve"], "POST"),
    (["pr", "ready", "7"], "POST"),
    (["pr", "diff", "7", "--stat"], "GET"),
)


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


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_api_transport_pr_diff_stat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = [
        [{"filename": "a.py", "additions": 3, "deletions": 1}],
    ]
    transport = GhApiTransport(repo="owner/repo")

    text = transport.run(["pr", "diff", "7", "--stat"])

    assert "1 file changed" in text
    assert FakeClient.calls[0][0:2] == ("GET", "/repos/owner/repo/pulls/7/files")


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_api_transport_repo_pull_request_templates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    import base64

    body = base64.b64encode(b"Bugfix body\n").decode("ascii")
    FakeClient.responses = [
        {"default_branch": "main"},
        [],
        {"content": body, "encoding": "base64", "name": "pull_request_template.md"},
    ]
    transport = GhApiTransport(repo="owner/repo")

    payload = transport.run_json(["repo", "view", "--json", "pullRequestTemplates"])

    assert payload["pullRequestTemplates"][0]["body"] == "Bugfix body\n"


@pytest.mark.parametrize(("argv", "expected_method"), PARITY_P0_API_COMMANDS)
@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_api_transport_p0_commands(
    argv: list[str],
    expected_method: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    if argv[:2] == ["pr", "diff"]:
        FakeClient.responses = [[{"filename": "a.py", "additions": 1, "deletions": 0}]]
        transport = GhApiTransport(repo="owner/repo")
        transport.run(argv)
        assert FakeClient.calls[0][0] == expected_method
        return
    FakeClient.responses = [
        [] if argv[1] == "list" else {"number": 7, "head": {"sha": "abc"}, "node_id": "PR_1"},
        {"check_runs": [{"name": "ci", "status": "completed"}]} if argv[1] == "checks" else None,
        {"id": "REV_1"} if argv[1] == "review" else None,
        {"data": {"markPullRequestReadyForReview": {"pullRequest": {"id": "PR_1"}}}}
        if argv[1] == "ready"
        else None,
    ]
    FakeClient.responses = [row for row in FakeClient.responses if row is not None]
    transport = GhApiTransport(repo="owner/repo")

    transport.run_json(argv)

    call_idx = 1 if argv[:2] == ["pr", "ready"] else 0
    assert FakeClient.calls[call_idx][0] == expected_method
