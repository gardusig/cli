"""Tests for tasks.pairs.json manifest loading and build."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.models.task import TaskPair
from cli.services.notion_pairs import (
    build_from_disk,
    combine_task,
    load_pairs,
    pair_deploy_rollout,
    pair_file_warning,
    save_pairs,
    scan_task_root,
    slugify,
    task_name,
)
from cli.services.notion_sync import build_pairs_manifest
from cli.integration.workspaces import notion_task_fixture_dir
from cli.services.notion_markdown import normalize_task_body, strip_leading_title_heading

FIXTURE_ROOT = notion_task_fixture_dir()


def test_load_pairs_fixture() -> None:
    pairs = load_pairs(FIXTURE_ROOT / "tasks.pairs.json", task_root=FIXTURE_ROOT)
    sample = next(p for p in pairs if p.header_filepath == "header/sample.yaml")
    assert task_name(sample, FIXTURE_ROOT) == "🧪 sample task"
    assert len([p for p in pairs if pair_file_warning(p, FIXTURE_ROOT) is None]) == 1


def test_load_pairs_rejects_duplicate_name(tmp_path: Path) -> None:
    manifest = tmp_path / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {"header_filepath": "m/a.yaml", "body_filepath": "b/a.md"},
                {"header_filepath": "m/b.yaml", "body_filepath": "b/b.md"},
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "m").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "m" / "a.yaml").write_text("name: same\n", encoding="utf-8")
    (tmp_path / "m" / "b.yaml").write_text("name: same\n", encoding="utf-8")
    (tmp_path / "b" / "a.md").write_text("body\n", encoding="utf-8")
    (tmp_path / "b" / "b.md").write_text("body\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_pairs(manifest, task_root=tmp_path)


def test_build_pairs_manifest_writes_under_task_root(tmp_path: Path) -> None:
    meta = tmp_path / "header" / "solo.yaml"
    body = tmp_path / "body" / "solo.md"
    meta.parent.mkdir(parents=True)
    body.parent.mkdir(parents=True)
    meta.write_text("name: Solo\n", encoding="utf-8")
    body.write_text("Body\n", encoding="utf-8")
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        f"notion:\n  task_root: {tmp_path}\n  pairs_file: tasks.pairs.json\n",
        encoding="utf-8",
    )

    result = build_pairs_manifest(tmp_path, config_dir=cfg_dir)

    manifest = tmp_path / "tasks.pairs.json"
    assert result.processed == 1
    assert manifest.is_file()
    pairs = load_pairs(manifest, task_root=tmp_path)
    assert task_name(pairs[0], tmp_path) == "Solo"


def test_build_pairs_manifest_writes_split_manifest(tmp_path: Path, monkeypatch) -> None:
    private_root = tmp_path / "private" / "tasks"
    meta = private_root / "header" / "solo.yaml"
    body = private_root / "body" / "solo.md"
    meta.parent.mkdir(parents=True)
    body.parent.mkdir(parents=True)
    meta.write_text("name: Solo\n", encoding="utf-8")
    body.write_text("Body\n", encoding="utf-8")
    repo_root = tmp_path / "repo"
    (repo_root / "config" / "notion").mkdir(parents=True)
    cfg_dir = repo_root / "config"
    (cfg_dir / "config.yaml").write_text(
        f"notion:\n  task_root: {private_root}\n  pairs_file: config/notion/tasks.pairs.json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("cli.utils.config.project_root", lambda: repo_root)

    result = build_pairs_manifest(private_root, config_dir=cfg_dir)

    manifest = repo_root / "config" / "notion" / "tasks.pairs.json"
    assert result.processed == 1
    assert manifest.is_file()
    pairs = load_pairs(manifest, task_root=private_root)
    assert task_name(pairs[0], private_root) == "Solo"


def test_build_from_disk_requires_name(tmp_path: Path) -> None:
    meta = tmp_path / "header" / "foo.yaml"
    body = tmp_path / "body" / "foo.md"
    meta.parent.mkdir(parents=True)
    body.parent.mkdir(parents=True)
    meta.write_text("name: Hello world\npriority: 2\n", encoding="utf-8")
    body.write_text("Describe the task.\n", encoding="utf-8")
    pairs = build_from_disk(tmp_path)
    assert task_name(pairs[0], tmp_path) == "Hello world"


def test_slugify_strips_emoji() -> None:
    assert slugify("🍳 kitchen") == "kitchen"


def test_save_pairs_path_only(tmp_path: Path) -> None:
    path = tmp_path / "tasks.pairs.json"
    pairs = [
        TaskPair(header_filepath="m/z.yaml", body_filepath="b/z.md"),
        TaskPair(header_filepath="m/a.yaml", body_filepath="b/a.md"),
    ]
    save_pairs(path, pairs)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded[0]["header_filepath"] == "m/a.yaml"
    assert "id" not in loaded[0]
    assert "name" not in loaded[0]


def test_normalize_task_body_strips_intro_and_title() -> None:
    md = "# 🍳 Kitchen\n\nEvery two weeks.\n\n## Steps\n\n1. Clean\n"
    out = normalize_task_body(md)
    assert out.startswith("## Steps")
    assert "Every two weeks" not in out


def test_pair_file_warning_orphan_header(tmp_path: Path) -> None:
    meta = tmp_path / "header" / "x.yaml"
    meta.parent.mkdir(parents=True)
    meta.write_text("name: x\n", encoding="utf-8")
    pair = TaskPair(header_filepath="header/x.yaml", body_filepath="body/x.md")
    assert pair_file_warning(pair, tmp_path) == "header without body: header/x.yaml"


def test_pair_deploy_rollout_disabled(tmp_path: Path) -> None:
    (tmp_path / "header").mkdir(parents=True)
    (tmp_path / "body").mkdir(parents=True)
    (tmp_path / "header" / "on.yaml").write_text("name: On\n", encoding="utf-8")
    (tmp_path / "body" / "on.md").write_text("## Steps\n", encoding="utf-8")
    (tmp_path / "header" / "off.yaml").write_text("name: Off\nenabled: false\n", encoding="utf-8")
    (tmp_path / "body" / "off.md").write_text("## Steps\n", encoding="utf-8")
    pairs = build_from_disk(tmp_path)
    rollout = pair_deploy_rollout(tmp_path, pairs)
    assert rollout.enabled == ["On"]
    assert rollout.disabled == ["Off"]
    assert rollout.broken == []


def test_strip_leading_title_heading() -> None:
    md = "# 🍳 Kitchen\n\nEvery two weeks.\n\n## Steps\n"
    assert strip_leading_title_heading(md).startswith("Every two weeks")
