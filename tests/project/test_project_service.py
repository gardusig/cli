from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from src.services.project_service import ProjectRef, ProjectService
from src.utils.config import ProjectConfig


def _config() -> ProjectConfig:
    return ProjectConfig.model_validate(
        {
            "default": {"owner": "owner", "number": 1, "project_id": "PVT_1"},
            "fields": {"status": "Status", "deadline": "Deadline", "type": "Type"},
            "lanes": {"todo": "Todo", "doing": "In Progress"},
        }
    )


def _service(provider: MagicMock | None = None, gh: MagicMock | None = None) -> ProjectService:
    return ProjectService(provider=provider or MagicMock(), gh_service=gh or MagicMock(), config=_config())


def test_project_read_commands_build_gh_project_args() -> None:
    provider = MagicMock()
    provider.run_json.return_value = [{"id": "PVT_1"}]
    svc = _service(provider)

    assert svc.project_list(owner="owner") == [{"id": "PVT_1"}]
    provider.run_json.assert_called_with(
        ["list", "--owner", "owner", "--limit", "30", "--format", "json"]
    )

    svc.field_list(ProjectRef(owner="owner", number=1))
    provider.run_json.assert_called_with(
        ["field-list", "1", "--owner", "owner", "--format", "json"]
    )


def test_project_crud_commands_build_gh_project_args() -> None:
    provider = MagicMock()
    provider.run_json.return_value = {"number": 1}
    svc = _service(provider)

    svc.project_create(owner="owner", title="Roadmap")
    provider.run_json.assert_called_with(["create", "--owner", "owner", "--title", "Roadmap", "--format", "json"])

    svc.project_edit(1, owner="owner", title="Renamed", visibility="private")
    provider.run_json.assert_called_with(
        ["edit", "1", "--owner", "owner", "--title", "Renamed", "--visibility", "private", "--format", "json"]
    )

    svc.project_delete(1, owner="owner")
    provider.run_json.assert_called_with(["delete", "1", "--owner", "owner", "--format", "json"])


def test_project_node_uses_shared_graphql_transport() -> None:
    gh = MagicMock()
    gh.provider.graphql.return_value = {
        "data": {
            "user": {"projectV2": {"id": "PVT_1", "title": "Roadmap", "number": 1}},
            "organization": None,
        }
    }
    svc = _service(gh=gh)

    node = svc.project_node(ProjectRef(owner="owner", number=1))

    assert node["id"] == "PVT_1"
    gh.provider.graphql.assert_called_once()


def test_item_status_resolves_lane_alias_to_single_select_option() -> None:
    provider = MagicMock()
    provider.run_json.side_effect = [
        {
            "fields": [
                {
                    "id": "FIELD_STATUS",
                    "name": "Status",
                    "options": [{"id": "OPT_TODO", "name": "Todo"}],
                }
            ]
        },
        {"id": "ITEM_1"},
    ]
    svc = _service(provider)

    svc.item_status(ProjectRef(owner="owner", number=1, project_id="PVT_1"), item_id="ITEM_1", status="todo")

    assert provider.run_json.call_args_list[-1].args[0] == [
        "item-edit",
        "--project-id",
        "PVT_1",
        "--id",
        "ITEM_1",
        "--field-id",
        "FIELD_STATUS",
        "--single-select-option-id",
        "OPT_TODO",
        "--format",
        "json",
    ]


def test_spawn_dry_run_returns_plan_without_creating_issues(tmp_path: Path) -> None:
    manifest = tmp_path / "seed.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "owner": "owner",
                "project": 1,
                "items": [{"title": "One", "body": "", "labels": ["feature"], "status": "Todo"}],
            }
        ),
        encoding="utf-8",
    )
    gh = MagicMock()
    svc = _service(gh=gh)

    payload = svc.spawn(manifest, dry_run=True)

    assert payload["dry_run"] is True
    assert payload["items"][0]["action"] == "planned"
    gh.issue_create.assert_not_called()


def test_spawn_creates_issue_adds_to_project_and_sets_status(tmp_path: Path) -> None:
    body_file = tmp_path / "body.md"
    body_file.write_text("Body", encoding="utf-8")
    manifest = tmp_path / "seed.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "owner": "owner",
                "project": 1,
                "items": [
                    {
                        "title": "One",
                        "body_file": "body.md",
                        "labels": ["maintenance"],
                        "status": "todo",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    provider = MagicMock()
    provider.run_json.side_effect = [
        {"id": "ITEM_1"},
        {
            "fields": [
                {
                    "id": "FIELD_STATUS",
                    "name": "Status",
                    "options": [{"id": "OPT_TODO", "name": "Todo"}],
                }
            ]
        },
        {"id": "ITEM_1"},
    ]
    gh = MagicMock()
    gh.issue_create.return_value = {
        "number": 5,
        "url": "https://github.com/owner/repo/issues/5",
        "title": "One",
    }
    svc = _service(provider, gh)

    payload = svc.spawn(manifest)

    assert payload["items"][0]["action"] == "created"
    assert payload["items"][0]["item_id"] == "ITEM_1"
    gh.issue_create.assert_called_once()
    assert gh.issue_create.call_args.kwargs["body_file"] == body_file.resolve()


def test_pairs_status_enforces_maintenance_deadline_or_interval(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "docs.yaml").write_text(
        yaml.safe_dump({"name": "docs: weekly review", "tag": "maintenance"}),
        encoding="utf-8",
    )
    (root / "body" / "docs.yaml").write_text(
        yaml.safe_dump({"body": "Review docs"}),
        encoding="utf-8",
    )
    manifest = root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "header_filepath": "header/docs.yaml",
                    "body_filepath": "body/docs.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )
    svc = _service()

    status = svc.pairs_status(root=root, manifest=manifest)

    assert status.enabled == []
    assert "maintenance" in status.broken[0]


def test_recurrence_advance_respawns_closed_maintenance_issue(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "docs.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "docs: weekly review",
                "tag": "maintenance",
                "interval": 7,
                "issue_number": 10,
            }
        ),
        encoding="utf-8",
    )
    (root / "body" / "docs.yaml").write_text(
        yaml.safe_dump({"body": "Review docs"}),
        encoding="utf-8",
    )
    manifest = root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "header_filepath": "header/docs.yaml",
                    "body_filepath": "body/docs.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )
    provider = MagicMock()
    provider.run_json.side_effect = [
        {"id": "ITEM_2"},
        {"fields": [{"id": "FIELD_DEADLINE", "name": "Deadline"}]},
        {"id": "ITEM_2"},
    ]
    gh = MagicMock()
    gh.issue_view.return_value = {"number": 10, "state": "CLOSED"}
    gh.issue_create.return_value = {
        "number": 11,
        "url": "https://github.com/owner/repo/issues/11",
        "title": "docs: weekly review",
    }
    svc = _service(provider, gh)

    payload = svc.recurrence_advance(
        root=root,
        manifest=manifest,
        ref=ProjectRef(owner="owner", number=1, project_id="PVT_1"),
    )

    assert payload["advanced"][0]["new_number"] == 11
    header = yaml.safe_load((root / "header" / "docs.yaml").read_text(encoding="utf-8"))
    assert header["previous_issue_number"] == 10
    assert header["issue_number"] == 11


def test_recurrence_advance_skips_open_maintenance_issue(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "docs.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "docs: weekly review",
                "tag": "maintenance",
                "interval": 7,
                "issue_number": 10,
            }
        ),
        encoding="utf-8",
    )
    (root / "body" / "docs.yaml").write_text(
        yaml.safe_dump({"body": "Review docs"}),
        encoding="utf-8",
    )
    manifest = root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "header_filepath": "header/docs.yaml",
                    "body_filepath": "body/docs.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )
    gh = MagicMock()
    gh.issue_view.return_value = {"number": 10, "state": "OPEN"}
    svc = _service(gh=gh)

    payload = svc.recurrence_advance(
        root=root,
        manifest=manifest,
        ref=ProjectRef(owner="owner", number=1, project_id="PVT_1"),
    )

    assert payload["advanced"] == []
    gh.issue_create.assert_not_called()


def test_ingest_pairs_updates_runtime_fields(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "docs.yaml").write_text(
        yaml.safe_dump({"name": "docs: weekly review", "tag": "maintenance", "issue_number": 10}),
        encoding="utf-8",
    )
    (root / "body" / "docs.yaml").write_text(
        yaml.safe_dump({"body": "body"}),
        encoding="utf-8",
    )
    manifest = root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps([{"header_filepath": "header/docs.yaml", "body_filepath": "body/docs.yaml"}]),
        encoding="utf-8",
    )
    provider = MagicMock()
    provider.run_json.return_value = [
        {
            "id": "ITEM_1",
            "status": "In Progress",
            "content": {"number": 10, "title": "docs: weekly review", "type": "Issue"},
            "fieldValues": [
                {"name": "2026-08-01", "field": {"name": "Deadline"}},
            ],
        }
    ]
    gh = MagicMock()
    gh.issue_view.return_value = {"number": 10, "labels": [{"name": "maintenance"}, {"name": "recurrence:docs-weekly"}]}
    svc = _service(provider, gh)

    payload = svc.ingest_pairs(root=root, manifest=manifest, ref=ProjectRef(owner="owner", number=1))

    assert payload["updated"] == ["docs: weekly review"]
    header = yaml.safe_load((root / "header" / "docs.yaml").read_text(encoding="utf-8"))
    assert header["forced_status"] == "In Progress"
    assert header["deadline"] == "2026-08-01"
    assert "maintenance" in header["labels"]


def test_deploy_pairs_continues_after_failure_and_sorts_maintenance_first(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "header").mkdir(parents=True)
    (root / "body").mkdir()
    (root / "header" / "feature.yaml").write_text(
        yaml.safe_dump({"name": "Add OAuth", "tag": "feature", "enabled": True}),
        encoding="utf-8",
    )
    (root / "header" / "docs.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "docs: weekly review",
                "tag": "maintenance",
                "interval": 7,
                "deadline": "2026-07-12",
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )
    (root / "body" / "feature.yaml").write_text(
        yaml.safe_dump({"body": "feature"}),
        encoding="utf-8",
    )
    (root / "body" / "docs.yaml").write_text(
        yaml.safe_dump({"body": "docs"}),
        encoding="utf-8",
    )
    manifest = root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {"header_filepath": "header/feature.yaml", "body_filepath": "body/feature.yaml"},
                {"header_filepath": "header/docs.yaml", "body_filepath": "body/docs.yaml"},
            ]
        ),
        encoding="utf-8",
    )
    provider = MagicMock()

    def provider_json(args):
        if args and args[0] == "field-list":
            return {
                "fields": [
                    {
                        "id": "FIELD_STATUS",
                        "name": "Status",
                        "options": [{"id": "OPT_TODO", "name": "Todo"}],
                    },
                    {"id": "FIELD_DEADLINE", "name": "Deadline"},
                ]
            }
        return {"id": "ITEM_1"}

    provider.run_json.side_effect = provider_json
    gh = MagicMock()
    created_titles: list[str] = []

    def issue_create(**kwargs):
        title = kwargs["title"]
        created_titles.append(title)
        if title == "Add OAuth":
            raise RuntimeError("rate limited")
        return {"number": 11, "url": "https://github.com/o/r/issues/11", "title": title}

    gh.issue_create.side_effect = issue_create
    svc = _service(provider, gh)

    payload = svc.deploy_pairs(root=root, manifest=manifest, ref=ProjectRef(owner="owner", number=1))

    assert created_titles == ["docs: weekly review", "Add OAuth"]
    assert len(payload["results"]) == 1
    assert payload["results"][0]["action"] == "created"
    assert len(payload["failed"]) == 1
    assert payload["failed"][0]["name"] == "Add OAuth"
