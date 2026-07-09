from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import yaml
import pytest

from src.services.gh_issues_sync import deploy_issues, ingest_issues, prune_issues


def _task_root(tmp_path: Path) -> Path:
    root = tmp_path / "tasks"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "one.yaml").write_text(
        "name: One\npriority: 2\ntag: hygiene\n", encoding="utf-8"
    )
    (root / "body" / "one.md").write_text("## Steps\n\nDo it.\n", encoding="utf-8")
    (root / "tasks.pairs.json").write_text(
        json.dumps([{"header_filepath": "header/one.yaml", "body_filepath": "body/one.md"}]),
        encoding="utf-8",
    )
    (root / "labels.manifest.yaml").write_text(yaml.safe_dump({"labels": []}), encoding="utf-8")
    return root


def _config(tmp_path: Path, root: Path, repo: str = "gardusig/private") -> Path:
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    (cfg / "config.yaml").write_text(
        f"""
notion:
  task_root: {root}
  pairs_file: tasks.pairs.json
gh:
  issues:
    repo: {repo}
    labels_manifest: labels.manifest.yaml
""",
        encoding="utf-8",
    )
    return cfg


def test_deploy_issues_dry_run(monkeypatch, tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    cfg = _config(tmp_path, root)
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg))
    svc = MagicMock()
    svc.issue_list_all.return_value = [{"number": 5, "title": "Old"}]

    result = deploy_issues(svc=svc, dry_run=True)

    assert result.deleted == [5]
    assert result.created[0]["title"] == "One"
    assert "priority:2" in result.created[0]["labels"]
    svc.issue_delete.assert_not_called()


def test_issue_sync_rejects_non_private_repo(monkeypatch, tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    cfg = _config(tmp_path, root, repo="gardusig/public")
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg))
    monkeypatch.delenv("CLI_GH_ISSUES_DEPLOY_ALLOW", raising=False)

    with pytest.raises(RuntimeError, match="restricted to repositories named 'database'"):
        deploy_issues(svc=MagicMock(), dry_run=True)


def test_ingest_issues_round_trip(monkeypatch, tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    cfg = _config(tmp_path, root)
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg))
    svc = MagicMock()
    svc.issue_list_all.return_value = [
        {
            "number": 7,
            "title": "Two",
            "body": "Imported body",
            "labels": [{"name": "issue-type:task"}, {"name": "priority:1"}],
        }
    ]

    result = ingest_issues(svc=svc)

    assert result.created == [{"title": "Two", "number": 7}]
    assert (root / "header" / "two.yaml").is_file()
    body_data = yaml.safe_load((root / "body" / "two.yaml").read_text(encoding="utf-8"))
    assert body_data["format"] == "markdown"
    assert body_data["body"] == "Imported body"
    manifest = json.loads((root / "tasks.pairs.json").read_text(encoding="utf-8"))
    assert {
        "header_filepath": "header/two.yaml",
        "body_filepath": "body/two.yaml",
    } in manifest


def test_prune_issues_filters_by_age(monkeypatch, tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    cfg = _config(tmp_path, root)
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg))
    old = (datetime.now(UTC) - timedelta(days=8)).isoformat().replace("+00:00", "Z")
    new = (datetime.now(UTC) - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    svc = MagicMock()
    svc.issue_list_all.return_value = [
        {"number": 1, "closedAt": old, "labels": []},
        {"number": 2, "closedAt": new, "labels": []},
    ]

    result = prune_issues(svc=svc, closed_older_than="7d")

    assert result.deleted == [1]
    svc.issue_delete.assert_called_once_with(1)
