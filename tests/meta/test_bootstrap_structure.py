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
    "scripts/git/branch.sh",
    "scripts/git/branch-list.sh",
    "scripts/git/branch-current.sh",
    "scripts/git/branch-prune.sh",
    "scripts/git/branch-rename.sh",
    "scripts/git/branch-delete.sh",
    "scripts/git/branch-delete-merged.sh",
    "scripts/git/branch-delete-all.sh",
    "scripts/git/branch-clear.sh",
    "scripts/git/cherry-pick.sh",
    "scripts/git/clean.sh",
    "scripts/git/commit.sh",
    "scripts/git/docs.sh",
    "scripts/git/large-files.sh",
    "scripts/git/main.sh",
    "scripts/git/post-merge-cleanup.sh",
    "scripts/git/pull.sh",
    "scripts/git/push.sh",
    "scripts/git/rebase.sh",
    "scripts/git/reset.sh",
    "scripts/git/revert.sh",
    "scripts/git/review.sh",
    "scripts/git/start.sh",
    "scripts/git/stash.sh",
    "scripts/git/tag.sh",
    "scripts/git/deploy.sh",
    "scripts/git/tag-list.sh",
    "scripts/git/tag-push.sh",
    "scripts/git/zip.sh",
    "scripts/drive/status.sh",
    "scripts/drive/ingest.sh",
    "scripts/drive/upload.sh",
    "scripts/drive/sync.sh",
]

GH_WORKFLOW_SCRIPTS = [
    "scripts/gh/_common.sh",
    "scripts/gh/README.md",
    "scripts/gh/backlog-next.sh",
    "scripts/gh/backlog-tree.sh",
    "scripts/gh/issue-view.sh",
    "scripts/gh/issue-context.sh",
    "scripts/gh/issue-close.sh",
    "scripts/gh/pr-create.sh",
    "scripts/gh/pr-view.sh",
    "scripts/gh/pr-list.sh",
    "scripts/gh/pr-merge.sh",
    "scripts/gh/sync-labels.sh",
    "scripts/gh/labelize-backlog.sh",
    "scripts/gh/issue-list.sh",
    "scripts/gh/issue-search.sh",
    "scripts/gh/issue-create.sh",
    "scripts/gh/issue-edit.sh",
    "scripts/gh/issue-comment.sh",
    "scripts/gh/issue-batch.sh",
    "scripts/gh/backlog-resequence.sh",
    "scripts/gh/label-list.sh",
    "scripts/gh/pr-diff.sh",
    "scripts/gh/pr-edit.sh",
    "scripts/gh/pr-close.sh",
    "scripts/gh/repo-view.sh",
]

DOCKER_VERIFY_PATHS = [
    "Dockerfile",
    "scripts/docker/common.sh",
    "scripts/docker/run-unit.sh",
    "scripts/docker/run-integration.sh",
    "scripts/docker/run-release.sh",
    "scripts/test/unit.sh",
    "scripts/test/integration.sh",
    "scripts/test/smoke.sh",
    "scripts/test/tags.sh",
    "scripts/test/workflows.sh",
    "scripts/test/all.sh",
    "scripts/ci/version-check.sh",
    "tests/integration/check_workflows.py",
    ".github/workflows/test.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/release.yml",
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
    "scripts/docker/bootstrap.sh",
    "scripts/pypi/install.sh",
    "scripts/_common.sh",
    "scripts/pypi/_common.sh",
    "scripts/notion/_common.sh",
    "scripts/pypi/build.sh",
    "scripts/pypi/upload.sh",
    "scripts/pypi/release.sh",
    "scripts/pypi/publish.sh",
    "scripts/pypi/test.sh",
    "scripts/notion/release.sh",
    *GH_WORKFLOW_SCRIPTS,
    *DOCKER_VERIFY_PATHS,
    "scripts/chrome/ingest.sh",
    "scripts/chrome/deploy.sh",
    "scripts/chrome/export.sh",
    "scripts/chrome/import.sh",
    "scripts/notion/ingest.sh",
    "scripts/notion/deploy.sh",
    "scripts/notion/sync.sh",
    "scripts/notion/download.sh",
    "scripts/notion/upload.sh",
    "scripts/notion/export.sh",
    "scripts/notion/import.sh",
    "scripts/notion/cleanup.sh",
    "scripts/git/_common.sh",
    "src/cli.py",
    "src/__main__.py",
    *GIT_WRAPPER_SCRIPTS,
]


def test_required_paths_exist() -> None:
    for rel in REQUIRED_PATHS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_install_script_targets_pypi_package() -> None:
    text = (ROOT / "scripts/pypi/install.sh").read_text(encoding="utf-8")
    assert "gardusig-cli" in text
    assert "pip install" in text
    assert "_common.sh" in text
    assert "pip install -e" not in text


def test_bootstrap_is_runtime_only_by_default() -> None:
    bootstrap = (ROOT / "scripts/docker/bootstrap.sh").read_text()
    assert "CLI_BOOTSTRAP_DEV" in bootstrap
    assert 'pip install -e ".[dev]"' in bootstrap
    assert 'pip install -e .' in bootstrap


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
