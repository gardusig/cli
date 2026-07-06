from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services.project_service import ProjectRef
from src.utils.config import ProjectAutoLinkConfig

runner = CliRunner()


class FakeProjectService:
    def default_ref(self) -> ProjectRef:
        return ProjectRef(owner="owner", number=1, project_id="PVT_1")

    def ref(self, *, owner=None, number=None, project_id=None) -> ProjectRef:
        default = self.default_ref()
        return ProjectRef(
            owner=owner or default.owner,
            number=number if number is not None else default.number,
            project_id=project_id or default.project_id,
        )

    def snapshot_summary(self, ref=None):
        ref = ref or self.default_ref()
        return [f"owner: {ref.owner}", f"project: {ref.number}"]

    def spawn(self, file: Path, *, dry_run: bool = False):
        return {"file": str(file), "dry_run": dry_run, "items": [{"title": "One"}]}

    def item_add_issue(self, issue: int, ref: ProjectRef):
        return {"id": "ITEM_1", "issue": issue, "project": ref.number}

    def item_add_url(self, url: str, ref: ProjectRef):
        return {"id": "ITEM_1", "url": url, "project": ref.number}

    def item_status(self, ref: ProjectRef, *, item_id: str, status: str):
        return {"id": item_id, "status": status, "project": ref.number}


class FakeGhService:
    def snapshot_summary(self):
        return ["repo: owner/repo"]

    def issue_create(self, **kwargs):
        return {
            "number": 99,
            "url": "https://github.com/owner/repo/issues/99",
            "title": kwargs["title"],
        }


def test_project_help_is_registered() -> None:
    result = runner.invoke(app, ["project", "--help"])

    assert result.exit_code == 0
    assert "GitHub Projects" in result.output


def test_project_spawn_dry_run_outputs_json(monkeypatch, tmp_path: Path) -> None:
    from src.commands import project

    seed = tmp_path / "seed.yaml"
    seed.write_text("items: []\n", encoding="utf-8")
    monkeypatch.setattr(project, "_svc", lambda repo=None: FakeProjectService())

    result = runner.invoke(app, ["project", "--format", "json", "spawn", "--file", str(seed), "--dry-run"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True


def test_project_item_add_refuses_without_yes(monkeypatch) -> None:
    from src.commands import project

    monkeypatch.setattr(project, "_svc", lambda repo=None: FakeProjectService())

    result = runner.invoke(app, ["project", "item", "add", "--issue", "42"])

    assert result.exit_code == 1
    assert "Refusing write in non-interactive mode" in result.output


def test_gh_issue_create_no_project_preserves_existing_behavior(monkeypatch) -> None:
    from src.commands import gh

    monkeypatch.setattr(gh, "_svc", lambda repo=None, transport="cli": FakeGhService())

    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "No board", "--no-project", "--yes"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["number"] == 99
    assert "project" not in payload


def test_gh_issue_create_auto_links_when_configured(monkeypatch) -> None:
    from src.commands import gh

    monkeypatch.setattr(gh, "_svc", lambda repo=None, transport="cli": FakeGhService())
    monkeypatch.setattr(
        gh,
        "project_auto_link",
        lambda: ProjectAutoLinkConfig(enabled=True, default_lane="todo", on_issue_create=True),
    )
    monkeypatch.setattr(gh, "ProjectService", lambda repo=None: FakeProjectService())

    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "Board item", "--yes"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["project"]["item_id"] == "ITEM_1"
    assert payload["project"]["lane"] == "todo"


def test_project_link_alias_adds_issue(monkeypatch) -> None:
    from src.commands import project

    monkeypatch.setattr(project, "_svc", lambda repo=None: FakeProjectService())

    result = runner.invoke(app, ["project", "link", "--issue", "42", "--yes"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["id"] == "ITEM_1"
    assert payload["issue"] == 42
