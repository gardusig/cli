"""Craft service tests (offline / stub DeepSeek)."""

from __future__ import annotations

import json

import pytest

from src.services.craft_ai import CraftAI, _ROLE
from src.services.issue_craft import (
    IssueCraftError,
    dedupe_candidate,
    epic_closure_status,
    find_plan_text,
    refresh_epic_checklist,
    render_epic_child_checklist,
    require_child_context,
    ship_issue,
)
from src.services.pr_craft import branch_name_for_issue, pr_execution_plan, review_pr


def test_three_model_roles_mapped() -> None:
    assert _ROLE["epic_review"] == "reason"
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


def test_epic_checklist_and_closure_status() -> None:
    children = [
        {"number": 2, "title": "1.1 — Done", "state": "CLOSED"},
        {"number": 3, "title": "1.2 — Next", "state": "OPEN", "blocked_by": [2]},
    ]
    checklist = render_epic_child_checklist(children)
    assert "- [x] #2 1.1 — Done" in checklist
    assert "- [ ] #3 1.2 — Next (blocked by #2)" in checklist
    refreshed = refresh_epic_checklist("Intro\n", children)
    assert "## Subissues / Closure checklist" in refreshed
    status = epic_closure_status(children)
    assert status["closeable"] is False
    assert status["open_children"][0]["number"] == 3


def test_require_child_context_rejects_epic_parent() -> None:
    with pytest.raises(IssueCraftError, match="epic issue"):
        require_child_context(
            {
                "issue": {"number": 1},
                "labels": ["issue-type:epic", "epic:wf"],
            }
        )


def test_pr_execution_plan_rejects_epic_parent(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    class FakeSvc:
        def issue_context(self, number: int) -> dict:
            return {
                "issue": {"number": number, "title": "1 — Epic", "body": ""},
                "labels": ["issue-type:epic", "epic:wf"],
                "comments": [],
            }

    with pytest.raises(IssueCraftError):
        pr_execution_plan(FakeSvc(), 1)


def test_pr_execution_plan_child(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    class FakeSvc:
        def issue_context(self, number: int) -> dict:
            return {
                "issue": {"number": number, "title": "1.1 — Child", "body": ""},
                "labels": ["issue-type:child", "epic:wf"],
                "comments": [{"body": "## [cli] plan\n\nDo it"}],
            }

    plan = pr_execution_plan(FakeSvc(), 2)
    assert plan["issue"] == 2
    assert plan["branch"].startswith("craft/2-")
    assert plan["plan_found"] is True


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
