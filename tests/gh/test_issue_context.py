"""Unit tests for gh issue context."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.services.gh_service import GhService


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
