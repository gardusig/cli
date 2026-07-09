"""Task runbook URL derivation from the private database repo."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.config import task_runbook_url


def test_task_runbook_url_uses_gh_issues_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "gh:\n  issues:\n    repo: gardusig/private\n"
        "notion:\n  link_branch: main\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))
    url = task_runbook_url("body/clean/kitchen.md")
    assert url == "https://github.com/gardusig/private/blob/main/tasks/body/clean/kitchen.md"


def test_task_runbook_url_respects_link_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "gh:\n  issues:\n    repo: gardusig/private\n"
        "notion:\n  link_branch: develop\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))
    url = task_runbook_url("header/misc/foo.yaml")
    assert url == "https://github.com/gardusig/private/blob/develop/tasks/header/misc/foo.yaml"
