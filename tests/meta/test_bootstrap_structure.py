"""Issue #3 bootstrap structure checks."""

from __future__ import annotations

from tests.constants import ROOT

import importlib
from pathlib import Path

from typer.testing import CliRunner

from src.cli import app


runner = CliRunner()

PROVIDER_MODULES = [
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

DOCKER_VERIFY_PATHS = [
    "scripts/pull-request/integration-smoke.sh",
]

REQUIRED_PATHS = [
    "config/config.yaml",
    "config/release/config.yaml",
    "config/notion/tasks.pairs.json",
    "config/notion/templates/body.md",
    "config/notion/templates/header.yaml",
    "config/config.test.yaml",
    "config/drives.yaml",
    "coverage-unit.ini",
    "tests/fixtures/bookmarks.html",
    "tests/fixtures/notion/tasks/tasks.pairs.json",
    "tests/fixtures/notion/tasks/header/sample.yaml",
    "tests/fixtures/notion/tasks/body/sample.md",
    "tests/fixtures/notion/workspace/tasks.pairs.json",
    *DOCKER_VERIFY_PATHS,
    "src/cli.py",
    "src/__main__.py",
    "src/services/toolkit/handlers.py",
    "src/services/toolkit/runner.py",
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
    assert cfg.backup.tags_dir == ".integration-scratch/ci-tags"
    assert cfg.drives.google.enabled is True
    assert cfg.chrome.profile == "Default"
