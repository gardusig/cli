"""Projects policy and parent/child tree tests."""

from __future__ import annotations

import pytest

from src.providers.gh import GhProvider
from src.services.gh_policy import RulesetForbiddenError, check_gh_args
from src.services.gh_topo import build_parent_child_tree, load_priority_levels


def test_gh_provider_allows_project_commands() -> None:
    check_gh_args(["project", "list"])


def test_gh_provider_blocks_ruleset_commands() -> None:
    provider = GhProvider()
    with pytest.raises(RulesetForbiddenError):
        provider.run(["ruleset", "list"])


def test_priority_levels_loaded() -> None:
    levels = load_priority_levels()
    assert len(levels) >= 5
    assert levels[1]["number"] == 1
    assert "explanation" in levels[1]


def test_build_parent_child_tree() -> None:
    issues = [
        {
            "number": 10,
            "state": "OPEN",
            "title": "Hub operator",
            "labels": ["issue-type:epic", "epic:hub-operator", "priority:1"],
        },
        {
            "number": 11,
            "state": "OPEN",
            "title": "2 — Runner image",
            "labels": ["issue-type:child", "epic:hub-operator"],
            "body": "",
        },
        {
            "number": 12,
            "state": "OPEN",
            "title": "1 — Merge pipeline",
            "labels": ["issue-type:child", "epic:hub-operator"],
            "body": "",
        },
    ]
    tree = build_parent_child_tree(issues)
    assert len(tree["parents"]) == 1
    parent = tree["parents"][0]
    assert parent["number"] == 10
    assert parent["children"][0]["step"] == 1
    assert parent["children"][1]["step"] == 2
