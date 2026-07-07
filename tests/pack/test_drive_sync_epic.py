"""Pack tests — Drive sync epic (#30)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_drive_sync_plan_helper_exists() -> None:
    text = (ROOT / "src" / "services" / "backup_repository.py").read_text(encoding="utf-8")
    assert "def plan_ingest_repositories" in text


def test_drive_sync_status_flag_registered() -> None:
    text = (ROOT / "src" / "commands" / "drive.py").read_text(encoding="utf-8")
    assert '"--status"' in text or "--status" in text


@requires_docs
def test_drive_sync_docs() -> None:
    text = (ROOT / "docs" / "drive.md").read_text(encoding="utf-8")
    assert "drive sync --status" in text
    assert "drive sync --dry-run" in text
    assert "primary" in text.lower() or "Primary" in text
