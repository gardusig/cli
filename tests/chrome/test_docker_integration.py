"""Chrome bookmark export/import in an isolated workspace (no repo data/)."""

from __future__ import annotations

from tests.constants import ROOT

import subprocess
from pathlib import Path

import pytest

from src.integration.workspaces import API_WORKSPACES
from tests.harness.chrome_harness import chrome_bookmarks_env
from tests.harness.integration_harness import copy_fixture_workspace, protected_repo_guard

CHROME_WS = next(w for w in API_WORKSPACES if w.name == "chrome")


@pytest.mark.integration
def test_export_bookmarks_from_downloads_fixture(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(CHROME_WS, tmp_path)
    env = chrome_bookmarks_env(workspace, ROOT)
    bookmarks_file = Path(env["CLI_BOOKMARKS_FILE"])

    with protected_repo_guard(CHROME_WS):
        subprocess.run(
            ["bash", str(ROOT / "src/scripts/chrome/export.sh")],
            env=env,
            check=True,
            cwd=ROOT,
        )

    assert bookmarks_file.is_file()
    text = bookmarks_file.read_text(encoding="utf-8")
    assert "Cli Test Bookmark" in text
    assert "example.com/cli-test" in text


@pytest.mark.integration
def test_import_bookmarks_script_runs(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(CHROME_WS, tmp_path)
    env = chrome_bookmarks_env(workspace, ROOT)
    bookmarks_file = Path(env["CLI_BOOKMARKS_FILE"])

    subprocess.run(
        ["bash", str(ROOT / "src/scripts/chrome/export.sh")],
        env=env,
        check=True,
        cwd=ROOT,
    )

    with protected_repo_guard(CHROME_WS):
        result = subprocess.run(
            ["bash", str(ROOT / "src/scripts/chrome/import.sh")],
            env=env,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    assert result.returncode == 0
    assert "Import complete" in result.stdout + result.stderr
    assert bookmarks_file.is_file()
