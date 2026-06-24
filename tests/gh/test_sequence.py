from tests.constants import ROOT

"""Unit tests for gh_sequence helpers."""

from src.services.gh_sequence import SequenceKey, next_child_issue, sort_issues_by_sequence


def test_sequence_key_loose_prefix() -> None:
    assert SequenceKey.from_title("3.4 Loose title") == SequenceKey(3, 4)


def test_sequence_key_prefix_minor() -> None:
    assert SequenceKey(2, 1).prefix() == "2.1 —"
    assert SequenceKey(2, None).prefix() == "2 —"


def test_next_child_issue_from_sequence_titles() -> None:
    issues = [
        {"number": 2, "title": "1.2 — Later", "labels": []},
        {"number": 1, "title": "1.1 — First", "labels": []},
    ]
    nxt = next_child_issue(issues)
    assert nxt is not None
    assert nxt["number"] == 1


def test_next_child_issue_none_when_empty() -> None:
    assert next_child_issue([]) is None


def test_sort_issues_unsequenced_last() -> None:
    issues = [
        {"number": 1, "title": "no prefix"},
        {"number": 2, "title": "1 — Epic"},
    ]
    ordered = sort_issues_by_sequence(issues)
    assert ordered[0]["number"] == 2
