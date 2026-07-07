"""Pack tests — Chrome Photos epic (#50)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_chrome_photos_service_exists() -> None:
    assert (ROOT / "src" / "services" / "photos_sync.py").is_file()


@requires_docs
def test_chrome_photos_docs() -> None:
    text = (ROOT / "docs" / "chrome.md").read_text(encoding="utf-8")
    assert "chrome photos ingest" in text
    assert "photos_dir" in text
    assert "Takeout" in text


def test_chrome_photos_commands_registered() -> None:
    catalog = (ROOT / "src" / "utils" / "catalog.py").read_text(encoding="utf-8")
    assert '"photos list"' in catalog or "photos list" in catalog
    assert "photos_sync" in (ROOT / "src" / "services" / "test_packages.py").read_text(encoding="utf-8")
