"""Pack tests — Epic 03 Notion backlog (#20–#23, #31)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_notion_sync_service_exists() -> None:
    text = (ROOT / "src" / "services" / "notion_sync.py").read_text(encoding="utf-8")
    assert "def export_tasks" in text
    assert "def import_tasks" in text
    assert "def cleanup_board" in text


def test_notion_commands_registered() -> None:
    text = (ROOT / "src" / "commands" / "notion.py").read_text(encoding="utf-8")
    for command in ("ingest", "deploy", "sync", "cleanup"):
        assert f'@notion_app.command("{command}")' in text or f'command("{command}")' in text


def test_notion_integration_checks_registered() -> None:
    checks = (ROOT / "src" / "integration" / "cli_api_checks.py").read_text(encoding="utf-8")
    for label in (
        "notion ingest",
        "notion deploy",
        "notion sync",
        "notion cleanup",
        "notion pairs build",
    ):
        assert label in checks


def test_notion_test_suite_present() -> None:
    notion_tests = ROOT / "tests" / "notion"
    assert notion_tests.is_dir()
    assert list(notion_tests.glob("test_*.py"))


@requires_docs
def test_notion_child_issue_docs() -> None:
    text = (ROOT / "docs" / "notion.md").read_text(encoding="utf-8")
    assert "NOTION_TOKEN" in text
    assert "cli notion ingest" in text
    assert "cli notion deploy" in text
    assert "cli notion sync" in text
    assert "cli notion cleanup" in text
    for issue in ("#20", "#21", "#22", "#23", "#31"):
        assert issue in text
