"""Shared pytest fixtures and markers."""

from __future__ import annotations

import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest


@lru_cache(maxsize=1)
def _git_subprocess_available() -> bool:
    """True when `git init` works (false in some sandboxes)."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["git", "init", "-b", "main", tmp],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_git: needs working git subprocess (skipped in restricted sandboxes)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _git_subprocess_available():
        return
    skip = pytest.mark.skip(reason="git subprocess not available in this environment")
    for item in items:
        if "requires_git" in item.keywords:
            item.add_marker(skip)
