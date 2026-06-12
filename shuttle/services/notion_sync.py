"""Notion task board sync — export / import / cleanup (API stubs)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shuttle.utils.config import NotionConfig


@dataclass
class NotionSyncResult:
    processed: int = 0
    skipped: int = 0
    failed: int = 0


def export_tasks(
    task_dir: Path,
    *,
    token: str,
    config: NotionConfig,
) -> NotionSyncResult:
    """Notion → local: write one markdown file per task under task_dir."""
    _ = (task_dir, token, config)
    raise NotImplementedError(
        "Notion export not implemented yet. See https://github.com/gardusig/shuttle-cli/issues/2"
    )


def import_tasks(
    task_dir: Path,
    *,
    token: str,
    config: NotionConfig,
    cleanup_first: bool | None = None,
) -> NotionSyncResult:
    """Local → Notion: create pages from markdown files in task_dir."""
    _ = (task_dir, token, config, cleanup_first)
    raise NotImplementedError(
        "Notion import not implemented yet. See https://github.com/gardusig/shuttle-cli/issues/2"
    )


def cleanup_board(
    *,
    token: str,
    config: NotionConfig,
) -> NotionSyncResult:
    """Archive every page in the configured Notion database."""
    _ = (token, config)
    raise NotImplementedError(
        "Notion cleanup not implemented yet. See https://github.com/gardusig/shuttle-cli/issues/2"
    )
