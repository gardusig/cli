"""Craft service tests (offline / stub DeepSeek)."""

from __future__ import annotations

import json

import pytest

from src.services.craft_ai import CraftAI, _ROLE
from src.services.issue_craft import dedupe_candidate, find_plan_text, ship_issue
from src.services.pr_craft import branch_name_for_issue, review_pr


def test_three_model_roles_mapped() -> None:
    assert _ROLE["issue_plan"] == "reason"
    assert _ROLE["pr_body"] == "chat"
    assert _ROLE["issue_dedupe"] == "categorize"


def test_craft_ai_stub_review(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    ai = CraftAI()
    out = ai.review_issue(context={"issue": {"number": 1, "title": "t"}}, open_issues=[])
    assert isinstance(out, str)
    data = json.loads(out)
    assert data.get("stub") or "Summary" in out or "summary" in out.lower()


def test_dedupe_stub(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    class FakeSvc:
        def issue_list(self, **kwargs):  # noqa: ANN003
            return [{"number": 5, "title": "existing", "labels": []}]

    verdict = dedupe_candidate(FakeSvc(), title="new", body="body")
    assert verdict.get("verdict") or verdict.get("parse_error") or verdict.get("stub")


def test_find_plan_text_from_comment() -> None:
    ctx = {
        "issue": {"body": "no plan"},
        "comments": [{"body": "## [cli] plan\n\nstep 1"}],
    }
    assert "## [cli] plan" in find_plan_text(ctx)


def test_branch_name_for_issue() -> None:
    assert branch_name_for_issue(42, "1 — Add hub workflows").startswith("craft/42-")


def test_ship_issue_dry_run(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    class FakeSvc:
        def repo_display(self) -> str:
            return "gardusig/cli"

        def issue_list(self, **kwargs):  # noqa: ANN003
            return []

        def backlog_tree(self) -> dict:
            return {"parents": []}

    result = ship_issue(FakeSvc(), title="1 — Test", body="body", yes=False)
    assert result["dry_run"] is True
    assert "dedupe" in result
