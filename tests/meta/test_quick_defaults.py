from tests.constants import ROOT

"""Quick default helpers."""

from unittest.mock import patch

from src.utils.quick_defaults import (
    default_commit_message,
    suggest_branch_name,
)


def test_suggest_branch_name_starts_at_one() -> None:
    with patch("src.utils.quick_defaults.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "260611"
        name = suggest_branch_name([])
    assert name == "wip-260611-001"


def test_suggest_branch_name_increments_sequence() -> None:
    with patch("src.utils.quick_defaults.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "260611"
        name = suggest_branch_name(["wip-260611-001", "wip-260611-002", "other"])
    assert name == "wip-260611-003"


def test_suggest_branch_name_skips_gaps() -> None:
    with patch("src.utils.quick_defaults.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "260611"
        name = suggest_branch_name(["wip-260611-005"])
    assert name == "wip-260611-006"


def test_default_commit_message_is_dot() -> None:
    assert default_commit_message() == "."
