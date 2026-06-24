"""Isolated PyPI build workspace (never mutates the repo under test)."""

from __future__ import annotations

from tests.constants import ROOT

import shutil
from pathlib import Path

from gardusig_cli.integration.docker_guard import integration_temp_dir


_COPY_NAMES = ("pyproject.toml", "README.md", "LICENSE", "requirements.txt")


def create_pypi_workspace() -> Path:
    """Copy minimal project tree into integration scratch for real builds."""
    workspace = integration_temp_dir("cli-pypi-")
    for name in _COPY_NAMES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, workspace / name)
    shutil.copytree(ROOT / "gardusig_cli", workspace / "gardusig_cli")
    return workspace


def read_repo_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("version ="):
            return line.split('"')[1]
    raise AssertionError("version not found in pyproject.toml")
