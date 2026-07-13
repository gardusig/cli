"""Pack tests — release version and doc smoke."""

from __future__ import annotations

from pathlib import Path

import tomllib

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_release_epic_version_matches_init() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = data["project"]["version"]
    init = (ROOT / "src" / "__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{version}"' in init


@requires_docs
def test_release_epic_hardening_pointer() -> None:
    text = (ROOT / "docs" / "public-cli-hardening.md").read_text(encoding="utf-8")
    assert "Registry contracts" in text
    assert "public_endpoints.py" in text
    assert "integration_coverage.py" in text
    assert "gardusig/cli" in text


@requires_docs
def test_release_epic_cli_repo_urls() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://github.com/gardusig/cli" in text


@requires_docs
def test_release_epic_post_merge_release_docs() -> None:
    release = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "Post-merge release" in release
    assert "pull-request.yaml" in release
    assert "version-check" in release
    assert "testpypi-verify" in release or "testpypi-consumer" in release
    ci = (ROOT / "docs" / "ci-workflows.md").read_text(encoding="utf-8")
    assert "CI_INTEGRATION_TIMEOUT" in ci


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
