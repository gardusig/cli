"""Pack tests — Epic 06d release and backlog closure."""

from __future__ import annotations

from pathlib import Path

import tomllib

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_release_epic_version_is_1_0_4() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "1.0.4"
    init = (ROOT / "src" / "__init__.py").read_text(encoding="utf-8")
    assert '__version__ = "1.0.4"' in init


@requires_docs
def test_release_epic_hardening_pointer() -> None:
    text = (ROOT / "docs" / "public-cli-hardening.md").read_text(encoding="utf-8")
    assert "Epic 06d" in text
    assert "Chrome Photos" in text
    assert "#50" in text
    assert "Drive sync" in text or "#30" in text
    assert "Epic 04d" in text or "#12" in text
    assert "Epic 03d" in text or "#20" in text
    assert "Epic 02d" in text or "#27" in text
    assert "Epic 06e" in text or "Merge readiness" in text
    assert "Epic 06g" in text


@requires_docs
def test_release_epic_cli_repo_urls() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://github.com/gardusig/cli" in text


@requires_docs
def test_release_epic_post_merge_release_docs() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "Post-merge release" in text
    assert "cli release main --yes" in text
    assert "1.0.3" in text
    assert "PR #96" in text


def test_release_epic_pack_smokes_present() -> None:
    pack = ROOT / "tests" / "pack"
    for name in (
        "test_release_epic.py",
        "test_chrome_photos_epic.py",
        "test_chrome_bookmarks_epic.py",
        "test_drive_sync_epic.py",
        "test_drive_providers_epic.py",
        "test_notion_epic.py",
        "test_merge_readiness_epic.py",
    ):
        assert (pack / name).is_file(), name
