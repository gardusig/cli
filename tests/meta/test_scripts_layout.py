"""Shell scripts stay thin — no embedded Python in scripts/."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path


SCRIPTS = ROOT / "scripts"


def test_scripts_tree_has_no_embedded_python() -> None:
    for path in SCRIPTS.rglob("*.sh"):
        text = path.read_text(encoding="utf-8")
        assert "<<'PY'" not in text, f"embedded Python heredoc in {path.relative_to(ROOT)}"
        assert 'python3 - <<' not in text, f"embedded Python in {path.relative_to(ROOT)}"


def test_shared_common_is_sourced() -> None:
    for rel in (
        "git/_common.sh",
        "gh/_common.sh",
        "pypi/_common.sh",
        "notion/_common.sh",
    ):
        text = (SCRIPTS / rel).read_text(encoding="utf-8")
        assert "scripts/_common.sh" in text or "../_common.sh" in text or '_common.sh"' in text


def test_root_common_has_cli_resolution_only() -> None:
    text = (SCRIPTS / "_common.sh").read_text(encoding="utf-8")
    assert "resolve_cli" in text
    assert "require_pypi_token" not in text
    assert "require_notion_token" not in text


def test_pypi_common_has_token_helper() -> None:
    text = (SCRIPTS / "pypi/_common.sh").read_text(encoding="utf-8")
    assert "require_pypi_token" in text
    assert "PACKAGE_NAME" in text
    assert "require_notion_token" not in text


def test_notion_common_has_token_helper() -> None:
    text = (SCRIPTS / "notion/_common.sh").read_text(encoding="utf-8")
    assert "require_notion_token" in text
    assert "require_pypi_token" not in text


def test_pypi_upload_sources_pypi_common() -> None:
    text = (SCRIPTS / "pypi/upload.sh").read_text(encoding="utf-8")
    assert 'source "$(dirname "$0")/_common.sh"' in text
    assert "require_pypi_token" in text


def test_notion_release_sources_notion_common() -> None:
    text = (SCRIPTS / "notion/release.sh").read_text(encoding="utf-8")
    assert 'source "$(dirname "$0")/_common.sh"' in text
    assert "require_notion_token" in text
