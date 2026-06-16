"""Chrome bookmark export/import in an isolated workspace (no repo data/)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from shuttle.integration.workspaces import API_WORKSPACES
from tests.chrome_harness import chrome_bookmarks_env
from tests.integration_harness import copy_fixture_workspace, protected_repo_guard

CHROME_WS = next(w for w in API_WORKSPACES if w.name == "chrome")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_export_bookmarks_from_downloads_fixture(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(CHROME_WS, tmp_path)
    env = chrome_bookmarks_env(workspace, ROOT)
    bookmarks_file = Path(env["SHUTTLE_BOOKMARKS_FILE"])

    with protected_repo_guard(CHROME_WS):
        subprocess.run(
            ["bash", str(ROOT / "scripts/chrome/export-bookmarks.sh")],
            env=env,
            check=True,
            cwd=ROOT,
        )

    assert bookmarks_file.is_file()
    text = bookmarks_file.read_text(encoding="utf-8")
    assert "Shuttle Test Bookmark" in text
    assert "example.com/shuttle-test" in text


@pytest.mark.integration
def test_import_bookmarks_script_runs(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(CHROME_WS, tmp_path)
    env = chrome_bookmarks_env(workspace, ROOT)
    bookmarks_file = Path(env["SHUTTLE_BOOKMARKS_FILE"])

    subprocess.run(
        ["bash", str(ROOT / "scripts/chrome/export-bookmarks.sh")],
        env=env,
        check=True,
        cwd=ROOT,
    )

    with protected_repo_guard(CHROME_WS):
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/chrome/import-bookmarks.sh")],
            env=env,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    assert result.returncode == 0
    assert "Import complete" in result.stdout + result.stderr
    assert bookmarks_file.is_file()
