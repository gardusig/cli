"""Chat distill pipeline tests (offline)."""

from __future__ import annotations

import json

import pytest

from src.services.chat_distill import load_repo_catalog, run_categorize, run_r1_distill
from src.services.chat_session import ChatSession


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("CLI_CHAT_DIR", str(tmp_path))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    s = ChatSession.create("distill-test")
    s.set_summary("Plan cli operator hub")
    s.append("user", "breaking change in cli affects yugioh")
    return s


def test_load_repo_catalog() -> None:
    repos = load_repo_catalog()
    assert any(r["repo"] == "gardusig/cli" for r in repos)


def test_r1_distill_stub(session) -> None:
    data = run_r1_distill(session)
    assert "themes" in data or "raw_notes" in data or data.get("stub") is True
    assert session.artifact_path("distill-r1.json").is_file()


def test_categorize_stub(session) -> None:
    run_r1_distill(session)
    plan = run_categorize(session)
    assert "repos" in plan
    assert session.artifact_path("categorize.json").is_file()
    json.loads(session.artifact_path("categorize.json").read_text())
