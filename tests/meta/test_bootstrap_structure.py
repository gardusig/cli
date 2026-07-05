"""Issue #3 bootstrap structure checks."""

from __future__ import annotations

from tests.constants import ROOT

import importlib
from pathlib import Path

from typer.testing import CliRunner

from src.cli import app


runner = CliRunner()

PROVIDER_MODULES = [
    "src.providers.github",
    "src.providers.notion",
    "src.providers.chrome",
    "src.providers.google_drive",
    "src.providers.proton_drive",
    "src.providers.icloud_drive",
    "src.providers.onedrive",
]

MODEL_MODULES = [
    "src.models.backup",
    "src.models.bookmark",
    "src.models.repository",
    "src.models.task",
]

SERVICE_MODULES = [
    "src.services.drive_sync",
    "src.services.backup_repository",
    "src.services.notion_sync",
    "src.services.bookmark_sync",
    "src.services.git_archive",
]

UTIL_MODULES = [
    "src.utils.fs",
    "src.utils.hashing",
    "src.utils.retry",
    "src.utils.yaml",
    "src.utils.zip",
    "src.utils.confirm",
]

INTERNAL_MODULES = [
    "src.internal.read.safety",
    "src.internal.read.git",
    "src.internal.write.gate",
    "src.internal.write.git",
]

GIT_WRAPPER_SCRIPTS = [
    "src/scripts/git/branch.sh",
    "src/scripts/git/branch-list.sh",
    "src/scripts/git/branch-current.sh",
    "src/scripts/git/branch-prune.sh",
    "src/scripts/git/branch-rename.sh",
    "src/scripts/git/branch-delete.sh",
    "src/scripts/git/branch-delete-merged.sh",
    "src/scripts/git/branch-delete-all.sh",
    "src/scripts/git/branch-clear.sh",
    "src/scripts/git/cherry-pick.sh",
    "src/scripts/git/clean.sh",
    "src/scripts/git/commit.sh",
    "src/scripts/git/docs.sh",
    "src/scripts/git/large-files.sh",
    "src/scripts/git/main.sh",
    "src/scripts/git/post-merge-cleanup.sh",
    "src/scripts/git/pull.sh",
    "src/scripts/git/push.sh",
    "src/scripts/git/rebase.sh",
    "src/scripts/git/reset.sh",
    "src/scripts/git/revert.sh",
    "src/scripts/git/review.sh",
    "src/scripts/git/start.sh",
    "src/scripts/git/stash.sh",
    "src/scripts/git/tag.sh",
    "src/scripts/git/deploy.sh",
    "src/scripts/git/tag-list.sh",
    "src/scripts/git/tag-push.sh",
    "src/scripts/git/zip.sh",
    "src/scripts/drive/status.sh",
    "src/scripts/drive/ingest.sh",
    "src/scripts/drive/upload.sh",
    "src/scripts/drive/sync.sh",
]

GH_WORKFLOW_SCRIPTS = [
    "src/scripts/gh/_common.sh",
    "src/scripts/gh/README.md",
    "src/scripts/gh/backlog-next.sh",
    "src/scripts/gh/backlog-tree.sh",
    "src/scripts/gh/issue-view.sh",
    "src/scripts/gh/issue-context.sh",
    "src/scripts/gh/issue-close.sh",
    "src/scripts/gh/pr-create.sh",
    "src/scripts/gh/pr-view.sh",
    "src/scripts/gh/pr-list.sh",
    "src/scripts/gh/pr-merge.sh",
    "src/scripts/gh/sync-labels.sh",
    "src/scripts/gh/labelize-backlog.sh",
    "src/scripts/gh/issue-list.sh",
    "src/scripts/gh/issue-search.sh",
    "src/scripts/gh/issue-create.sh",
    "src/scripts/gh/issue-edit.sh",
    "src/scripts/gh/issue-comment.sh",
    "src/scripts/gh/issue-batch.sh",
    "src/scripts/gh/backlog-resequence.sh",
    "src/scripts/gh/label-list.sh",
    "src/scripts/gh/pr-diff.sh",
    "src/scripts/gh/pr-edit.sh",
    "src/scripts/gh/pr-close.sh",
    "src/scripts/gh/repo-view.sh",
]

DOCKER_VERIFY_PATHS = [
    "src/scripts/ci/version-check.sh",
    "tests/integration/check_workflows.py",
]

REQUIRED_PATHS = [
    "config/config.yaml",
    "config/gh/labels.manifest.yaml",
    "config/release/config.yaml",
    "config/notion/tasks.pairs.json",
    "config/notion/templates/body.md",
    "config/notion/templates/header.yaml",
    "config/ci/config.yaml",
    "config/drives.yaml",
    "coverage-unit.ini",
    "tests/fixtures/bookmarks.html",
    "tests/fixtures/notion/tasks/tasks.pairs.json",
    "tests/fixtures/notion/tasks/header/sample.yaml",
    "tests/fixtures/notion/tasks/body/sample.md",
    "tests/fixtures/notion/workspace/tasks.pairs.json",
    "src/scripts/_common.sh",
    "src/scripts/notion/_common.sh",
    "src/scripts/notion/release.sh",
    *GH_WORKFLOW_SCRIPTS,
    *DOCKER_VERIFY_PATHS,
    "src/scripts/chrome/ingest.sh",
    "src/scripts/chrome/deploy.sh",
    "src/scripts/chrome/export.sh",
    "src/scripts/chrome/import.sh",
    "src/scripts/notion/ingest.sh",
    "src/scripts/notion/deploy.sh",
    "src/scripts/notion/sync.sh",
    "src/scripts/notion/download.sh",
    "src/scripts/notion/upload.sh",
    "src/scripts/notion/export.sh",
    "src/scripts/notion/import.sh",
    "src/scripts/notion/cleanup.sh",
    "src/scripts/git/_common.sh",
    "src/cli.py",
    "src/__main__.py",
    *GIT_WRAPPER_SCRIPTS,
]


def test_required_paths_exist() -> None:
    for rel in REQUIRED_PATHS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_placeholder_modules_import() -> None:
    for name in (
        PROVIDER_MODULES + MODEL_MODULES + SERVICE_MODULES + UTIL_MODULES + INTERNAL_MODULES
    ):
        importlib.import_module(name)


def test_top_level_commands_registered() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("restore", "git", "drive", "notion", "chrome"):
        assert cmd in result.stdout


def test_config_loader() -> None:
    from src.utils.config import load_config

    cfg = load_config(ROOT / "config")
    assert cfg.backup.repositories
    assert cfg.drives.google.enabled is True
    assert cfg.chrome.profile == "Default"
