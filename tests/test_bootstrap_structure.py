"""Issue #3 bootstrap structure checks."""

from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from gardusig_cli.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()

PROVIDER_MODULES = [
    "gardusig_cli.providers.github",
    "gardusig_cli.providers.notion",
    "gardusig_cli.providers.chrome",
    "gardusig_cli.providers.google_drive",
    "gardusig_cli.providers.proton_drive",
    "gardusig_cli.providers.icloud_drive",
    "gardusig_cli.providers.onedrive",
]

MODEL_MODULES = [
    "gardusig_cli.models.backup",
    "gardusig_cli.models.bookmark",
    "gardusig_cli.models.repository",
    "gardusig_cli.models.task",
]

SERVICE_MODULES = [
    "gardusig_cli.services.drive_sync",
    "gardusig_cli.services.backup_repository",
    "gardusig_cli.services.notion_sync",
    "gardusig_cli.services.bookmark_sync",
    "gardusig_cli.services.git_archive",
]

UTIL_MODULES = [
    "gardusig_cli.utils.fs",
    "gardusig_cli.utils.hashing",
    "gardusig_cli.utils.retry",
    "gardusig_cli.utils.yaml",
    "gardusig_cli.utils.zip",
    "gardusig_cli.utils.confirm",
]

INTERNAL_MODULES = [
    "gardusig_cli.internal.read.safety",
    "gardusig_cli.internal.read.git",
    "gardusig_cli.internal.write.gate",
    "gardusig_cli.internal.write.git",
]

CURSOR_SKILLS_GIT_SCRIPTS = [
    "scripts/git/branch.sh",
    "scripts/git/branch-delete.sh",
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
    "scripts/git/tag-list.sh",
    "scripts/git/tag-push.sh",
    "scripts/git/zip.sh",
    "scripts/drive/status.sh",
    "scripts/drive/ingest.sh",
    "scripts/drive/upload.sh",
    "scripts/drive/sync.sh",
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
    ".github/workflows/test.yml",
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
    "scripts/bootstrap.sh",
    "scripts/install.sh",
    "scripts/_common.sh",
    "scripts/pypi/_common.sh",
    "scripts/pypi/build.sh",
    "scripts/pypi/upload.sh",
    "scripts/pypi/release.sh",
    "scripts/pypi/publish.sh",
    "scripts/pypi/test.sh",
    "scripts/notion/release.sh",
    "scripts/gh/sync-labels.sh",
    "scripts/gh/labelize-backlog.sh",
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
    "gardusig_cli/cli.py",
    "gardusig_cli/__main__.py",
    *CURSOR_SKILLS_GIT_SCRIPTS,
]


def test_required_paths_exist() -> None:
    for rel in REQUIRED_PATHS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_install_script_targets_pypi_package() -> None:
    text = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
    assert "gardusig-cli" in text
    assert "pip install" in text
    assert "find_python312" in text
    assert "pip install -e" not in text


def test_bootstrap_is_runtime_only_by_default() -> None:
    bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
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
    from gardusig_cli.utils.config import load_config

    cfg = load_config(ROOT / "config")
    assert cfg.backup.repositories
    assert cfg.drives.google.enabled is True
    assert cfg.chrome.profile == "Default"
