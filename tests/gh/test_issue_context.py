"""Unit tests for gh issue context."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.providers.gh_transport import GhApiTransport
from src.services.gh_service import GhService
from tests.gh.test_transport import FakeClient


def api_issue_context_responses() -> list[Any]:
    """REST sequence for issue context #2 (epic:wf-test fixture shape)."""
    return [
        {
            "number": 2,
            "title": "1.1 — First child",
            "body": "Child task. See also #3 for related work.",
            "labels": [{"name": "epic:wf-test"}, {"name": "issue-type:child"}],
        },
        [{"body": "Comment on #2"}],
        [
            {
                "number": 1,
                "title": "1 — Workflow epic",
                "labels": [{"name": "epic:wf-test"}, {"name": "issue-type:epic"}],
            },
            {
                "number": 2,
                "title": "1.1 — First child",
                "labels": [{"name": "epic:wf-test"}, {"name": "issue-type:child"}],
            },
            {
                "number": 3,
                "title": "1.2 — Second child",
                "labels": [{"name": "epic:wf-test"}, {"name": "issue-type:child"}],
            },
        ],
        {
            "number": 3,
            "title": "1.2 — Second child",
            "labels": [{"name": "epic:wf-test"}, {"name": "issue-type:child"}],
        },
    ]


@pytest.fixture
def svc() -> GhService:
    service = GhService(repo="owner/repo")
    service.provider = MagicMock()
    return service


def test_issue_context_epic_siblings_and_links(svc: GhService) -> None:
    svc.issue_view = MagicMock(
        side_effect=lambda n, comments=False: {
            2: {
                "number": 2,
                "title": "1.1 — Child",
                "body": "See #3",
                "labels": [{"name": "epic:wf"}, {"name": "issue-type:child"}],
                "comments": [{"body": "note"}] if comments else None,
            },
            1: {"number": 1, "title": "1 — Epic", "labels": []},
            3: {"number": 3, "title": "1.2 — Other", "labels": []},
        }[n]
    )
    svc.issue_list = MagicMock(
        return_value=[
            {
                "number": 1,
                "title": "1 — Epic",
                "labels": [{"name": "epic:wf"}, {"name": "issue-type:epic"}],
            },
            {
                "number": 2,
                "title": "1.1 — Child",
                "labels": [{"name": "epic:wf"}, {"name": "issue-type:child"}],
            },
            {
                "number": 3,
                "title": "1.2 — Other",
                "labels": [{"name": "epic:wf"}, {"name": "issue-type:child"}],
            },
        ]
    )

    ctx = svc.issue_context(2)
    assert ctx["epic"]["slug"] == "epic:wf"
    assert ctx["epic"]["parent"]["number"] == 1
    assert len(ctx["siblings"]) == 1
    assert ctx["siblings"][0]["number"] == 3
    assert ctx["linked_issues"][0]["number"] == 3
    assert ctx["comments"]


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_issue_context_api_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = api_issue_context_responses()
    svc = GhService(repo="example/repo", transport="api")

    ctx = svc.issue_context(2)

    assert ctx["epic"]["slug"] == "epic:wf-test"
    assert ctx["epic"]["parent"]["number"] == 1
    assert len(ctx["siblings"]) == 1
    assert ctx["siblings"][0]["number"] == 3
    assert ctx["linked_issues"][0]["number"] == 3
    assert ctx["comments"]
    assert FakeClient.calls[0][0:2] == ("GET", "/repos/example/repo/issues/2")
    assert FakeClient.calls[1][0:2] == ("GET", "/repos/example/repo/issues/2/comments")
    assert FakeClient.calls[2][0:2] == ("GET", "/repos/example/repo/issues")


@patch("src.providers.gh_transport.httpx.Client", FakeClient)
def test_issue_context_api_transport_cli_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typer.testing import CliRunner

    from src.cli import app

    monkeypatch.setenv("GITHUB_TOKEN", "token")
    FakeClient.responses = api_issue_context_responses()
    result = CliRunner().invoke(
        app,
        [
            "gh",
            "--transport",
            "api",
            "--repo",
            "example/repo",
            "--format",
            "json",
            "issue",
            "context",
            "2",
        ],
    )

    assert result.exit_code == 0, result.stdout or result.stderr
    assert "epic:wf-test" in result.stdout
