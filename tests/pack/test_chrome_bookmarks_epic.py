"""Pack tests — Epic 02 Chrome bookmarks backlog (#27, #28)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_chrome_bookmarks_snapshot_command_registered() -> None:
    text = (ROOT / "src" / "commands" / "chrome.py").read_text(encoding="utf-8")
    assert '@bookmarks_app.command("snapshot")' in text
    assert "snapshot_bookmarks" in text


def test_chrome_bookmarks_profiles_in_config_docs() -> None:
    text = (ROOT / "docs" / "chrome.md").read_text(encoding="utf-8")
    assert "profiles:" in text
    assert "snapshot_retention" in text
    assert "snapshots_dir" in text


@requires_docs
def test_chrome_bookmarks_child_issue_docs() -> None:
    chrome = (ROOT / "docs" / "chrome.md").read_text(encoding="utf-8")
    bookmarks = (ROOT / "docs" / "bookmarks.md").read_text(encoding="utf-8")
    assert "CLI_SKIP_CHROME_AUTOMATION" in chrome
    assert "CLI_BOOKMARKS_FILE" in chrome
    assert "github-pipelines" in chrome.lower() or "gardusig/cli" in chrome or "gardusig/pipelines" in chrome
    assert "chrome.md" in bookmarks
    assert "CLI_DOWNLOADS_DIR" in bookmarks or "CLI_BOOKMARKS" in bookmarks


def test_chrome_bookmarks_integration_checks() -> None:
    checks = (ROOT / "src" / "integration" / "cli_api_checks.py").read_text(encoding="utf-8")
    assert "chrome bookmarks ingest" in checks
    assert "chrome bookmarks snapshot" in checks or "bookmarks snapshot" in checks
