"""Unit tests for notion_pairs and notion_markdown internals."""

from __future__ import annotations

from pathlib import Path

import pytest

from gardusig_cli.models.task import TaskPair
from gardusig_cli.services.notion_markdown import (
    blocks_to_task_body,
    strip_content_before_steps,
    strip_leading_title_heading,
)
from gardusig_cli.services.notion_pairs import pair_file_warning, scan_task_root, slugify


def test_strip_content_before_steps_drops_preamble() -> None:
    md = "Intro cadence.\n\n## Steps\n\n1. Do thing\n"
    assert strip_content_before_steps(md).startswith("## Steps")


def test_strip_content_before_steps_passthrough_when_no_steps() -> None:
    md = "Only intro\n"
    assert strip_content_before_steps(md).strip() == "Only intro"


def test_blocks_to_task_body_trims_title_heading() -> None:
    blocks = [
        {
            "type": "heading_1",
            "heading_1": {"rich_text": [{"plain_text": "Task title", "type": "text"}]},
        },
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"plain_text": "Steps", "type": "text"}]},
        },
        {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"plain_text": "Step one", "type": "text"}],
                "checked": False,
            },
        },
    ]
    body = blocks_to_task_body(blocks, task_name="Task title")
    assert body.startswith("## Steps")
    assert "Step one" in body


def test_slugify_empty_title_falls_back_to_task() -> None:
    assert slugify("   ") == "task"


def test_pair_file_warning_missing_name(tmp_path: Path) -> None:
    meta = tmp_path / "header" / "x.yaml"
    body = tmp_path / "body" / "x.md"
    meta.parent.mkdir(parents=True)
    body.parent.mkdir(parents=True)
    meta.write_text("name: \n", encoding="utf-8")
    body.write_text("## Steps\n", encoding="utf-8")
    pair = TaskPair(header_filepath="header/x.yaml", body_filepath="body/x.md")
    warning = pair_file_warning(pair, tmp_path)
    assert warning is not None
    assert "header/x.yaml" in warning
    assert "name" in warning


def test_scan_task_root_warns_on_duplicate_names(tmp_path: Path) -> None:
    for name in ("a", "b"):
        meta = tmp_path / "header" / f"{name}.yaml"
        body = tmp_path / "body" / f"{name}.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        body.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text("name: same\n", encoding="utf-8")
        body.write_text("## Steps\n", encoding="utf-8")

    scan = scan_task_root(tmp_path)
    assert any("Duplicate task name" in w for w in scan.warnings)
    assert scan.pairs == []


def test_strip_leading_title_heading_keeps_body_without_h1() -> None:
    md = "## Steps\n\n1. x\n"
    assert strip_leading_title_heading(md) == md
