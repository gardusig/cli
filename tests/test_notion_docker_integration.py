"""Docker integration gate: Notion task pair deploy/ingest with mocked API.

Uses an isolated copy of tests/fixtures/notion/workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.integration.workspaces import API_WORKSPACES
from cli.services.notion_pairs import combine_task, load_pairs, pair_file_warning, scan_task_root, task_name
from cli.services.notion_sync import export_tasks, import_tasks
from cli.utils.config import NotionConfig
from tests.integration_harness import copy_fixture_workspace, protected_repo_guard
from tests.notion_harness import deploy_ok_handler, ingest_handler, notion_page, patch_notion_http

NOTION_WS = next(w for w in API_WORKSPACES if w.name == "notion")


@pytest.fixture
def isolated_task_root(tmp_path: Path) -> Path:
    """Copy workspace fixture into a temp task root (not repo data/)."""
    return copy_fixture_workspace(NOTION_WS, tmp_path, dest_name="notion-tasks")


@pytest.fixture
def notion_paths(monkeypatch, isolated_task_root: Path):
    manifest = isolated_task_root / "tasks.pairs.json"

    monkeypatch.setattr(
        "cli.services.notion_sync.notion_pairs_file",
        lambda config_dir=None: manifest,
    )
    monkeypatch.setattr(
        "cli.services.notion_sync.notion_task_root",
        lambda config_dir=None: isolated_task_root,
    )
    return isolated_task_root, manifest


@pytest.mark.integration
def test_scan_warns_on_orphan_metadata_and_body(isolated_task_root: Path) -> None:
    scan = scan_task_root(isolated_task_root)
    assert any("header without body" in w for w in scan.warnings)
    assert any("body without header" in w for w in scan.warnings)
    assert len(scan.pairs) == 3
    names = {task_name(p, isolated_task_root) for p in scan.pairs}
    assert names == {"✅ complete task", "⏸️ disabled task", "🧪 sample task"}


@pytest.mark.integration
def test_combine_task_iterates_complete_pairs(isolated_task_root: Path) -> None:
    scan = scan_task_root(isolated_task_root)
    tasks = [combine_task(pair, isolated_task_root) for pair in scan.pairs]
    assert len(tasks) == 3
    by_name = {t.metadata.name: t for t in tasks}
    assert by_name["✅ complete task"].body.startswith("## Steps")
    assert "Complete step" in by_name["✅ complete task"].body
    assert by_name["⏸️ disabled task"].metadata.enabled is False


@pytest.mark.integration
def test_deploy_mock_notion_200_iterates_tasks(notion_paths) -> None:
    task_root, _manifest = notion_paths
    created: list[dict] = []
    cfg = NotionConfig(database_id="db-docker", cleanup_before_deploy=False)

    with patch_notion_http(deploy_ok_handler(created)):
        result = import_tasks(
            task_root,
            token="tok",
            config=cfg,
            cleanup_first=False,
        )

    assert result.processed == 2
    assert result.skipped == 1
    assert any("header without body" in w for w in result.warnings)
    assert any("body without header" in w for w in result.warnings)
    assert len(created) == 2
    title = created[0]["properties"]["Name"]["title"][0]["text"]["content"]
    assert title == "✅ complete task"
    assert "Steps" in json.dumps(created[0].get("children", []))


@pytest.mark.integration
def test_ingest_mock_notion_writes_files_under_task_root(notion_paths, isolated_task_root: Path) -> None:
    task_root, manifest = notion_paths
    cfg = NotionConfig(database_id="db-docker")

    pages = [
        notion_page(page_id="p-existing", title="✅ complete task"),
        notion_page(page_id="p-new", title="🆕 notion-only task"),
    ]

    with patch_notion_http(ingest_handler(pages)):
        result = export_tasks(task_root, token="tok", config=cfg)

    assert result.processed == 2
    new_meta_files = list((task_root / "header/misc").glob("*.yaml"))
    assert new_meta_files
    assert any("notion-only" in p.stem for p in new_meta_files)

    pairs = load_pairs(manifest, task_root=task_root)
    names = {
        task_name(p, task_root)
        for p in pairs
        if pair_file_warning(p, task_root) is None
    }
    assert "🆕 notion-only task" in names

    updated = (task_root / "header/complete.yaml").read_text(encoding="utf-8")
    assert "2026-03-01" in updated


@pytest.mark.integration
def test_integration_uses_isolated_task_root_copy(notion_paths, isolated_task_root: Path) -> None:
    """Guard: integration runs against a temp copy, not the committed fixture tree."""
    from cli.integration.workspaces import fixture_dir

    repo_fixture = fixture_dir(NOTION_WS)
    assert isolated_task_root != repo_fixture
    assert not str(isolated_task_root).startswith(str(repo_fixture))

    cfg = NotionConfig(database_id="db-docker", cleanup_before_deploy=False)
    with protected_repo_guard(NOTION_WS):
        with patch_notion_http(deploy_ok_handler()):
            import_tasks(isolated_task_root, token="tok", config=cfg, cleanup_first=False)
