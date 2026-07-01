"""gh_topo backlog selection tests."""

from __future__ import annotations

from src.services.gh_topo import StepKey, epic_priority, pick_next_child, sort_children


def test_step_key_from_title() -> None:
    assert StepKey.from_title("3 — Runner image") == StepKey(3)


def test_epic_priority_label() -> None:
    issue = {"labels": ["priority:1", "epic:hub-operator"]}
    assert epic_priority(issue) == 1


def test_pick_next_child_by_step() -> None:
    issues = [
        {"number": 1, "state": "OPEN", "title": "Epic", "labels": ["issue-type:epic", "epic:foo", "priority:0"]},
        {"number": 2, "state": "OPEN", "title": "2 — Second", "labels": ["issue-type:child", "epic:foo"]},
        {"number": 3, "state": "OPEN", "title": "1 — First", "labels": ["issue-type:child", "epic:foo"]},
    ]
    picked = pick_next_child(issues)
    assert picked is not None
    assert picked["number"] == 3


def test_sort_children() -> None:
    issues = [
        {"number": 2, "title": "2 — B"},
        {"number": 1, "title": "1 — A"},
    ]
    ordered = sort_children(issues)
    assert ordered[0]["number"] == 1
