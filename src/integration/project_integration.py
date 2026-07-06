"""Integration checks for top-level ``cli project`` (mocked ProjectService)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from typer.testing import CliRunner

from src.cli import app
from src.integration.cli_api_checks import command_tokens
from src.services.project_service import ProjectPairStatus, ProjectRef

_CLI_RUNNER = CliRunner()

# Primary command paths covered by mocked integration (not every nested write variant).
PROJECT_COMMAND_PATHS: tuple[tuple[str, ...], ...] = (
    ("project", "list"),
    ("project", "spawn"),
    ("project", "pairs", "status"),
    ("project", "link"),
    ("project", "item", "add"),
    ("project", "deploy"),
    ("project", "ingest"),
    ("project", "sync"),
)

CheckKind = Literal["ok", "refuse"]

SEED_FIXTURE = "config/project/examples/seed.yaml"


class _FakeProjectService:
    def default_ref(self) -> ProjectRef:
        return ProjectRef(owner="owner", number=1, project_id="PVT_1")

    def ref(self, *, owner=None, number=None, project_id=None) -> ProjectRef:
        default = self.default_ref()
        return ProjectRef(
            owner=owner or default.owner,
            number=number if number is not None else default.number,
            project_id=project_id or default.project_id,
        )

    def snapshot_summary(self, ref=None) -> list[str]:
        ref = ref or self.default_ref()
        return [f"owner: {ref.owner}", f"project: {ref.number}"]

    def project_list(self, *, owner: str = "gardusig", limit: int = 30) -> list[dict[str, str]]:
        return [{"id": "PVT_1", "title": "Roadmap", "number": "1"}]

    def spawn(self, file: Path, *, dry_run: bool = False) -> dict[str, object]:
        return {"file": str(file), "dry_run": dry_run, "items": [{"title": "One"}]}

    def pairs_status(self, **kwargs: object) -> ProjectPairStatus:
        return ProjectPairStatus(enabled=["docs: weekly review"], disabled=[], broken=[])

    def item_add_issue(self, issue: int, ref: ProjectRef) -> dict[str, object]:
        return {"id": "ITEM_1", "issue": issue, "project": ref.number}

    def deploy_pairs(self, **kwargs: object) -> dict[str, object]:
        return {"results": [], "failed": []}

    def ingest_pairs(self, **kwargs: object) -> dict[str, object]:
        return {"updated": ["docs: weekly review"]}

    def sync_pairs(self, **kwargs: object) -> dict[str, object]:
        return {"ingest": {"updated": []}, "deploy": {"results": [], "failed": []}}


@dataclass(frozen=True)
class ProjectCheck:
    label: str
    args: tuple[str, ...]
    kind: CheckKind = "ok"
    needle: str | None = None
    failure: str | None = None


def project_checks() -> list[ProjectCheck]:
    return [
        ProjectCheck(
            "project list",
            ("project", "--format", "json", "list"),
            needle="PVT_1",
        ),
        ProjectCheck(
            "project spawn dry-run",
            ("project", "--format", "json", "spawn", "--file", SEED_FIXTURE, "--dry-run"),
            needle="dry_run",
        ),
        ProjectCheck(
            "project pairs status",
            ("project", "--format", "json", "pairs", "status"),
            needle="enabled",
        ),
        ProjectCheck(
            "project link",
            ("project", "--format", "json", "link", "--issue", "42", "--yes"),
            needle="ITEM_1",
        ),
        ProjectCheck(
            "project item add",
            ("project", "--format", "json", "item", "add", "--issue", "42", "--yes"),
            needle="ITEM_1",
        ),
        ProjectCheck(
            "project deploy",
            ("project", "--format", "json", "deploy", "--yes"),
            needle="results",
        ),
        ProjectCheck(
            "project link refuse",
            ("project", "link", "--issue", "42"),
            kind="refuse",
            needle="Refusing write",
            failure="refuse_gate",
        ),
        ProjectCheck(
            "project spawn refuse",
            ("project", "spawn", "--file", SEED_FIXTURE),
            kind="refuse",
            needle="Refusing write",
            failure="refuse_gate",
        ),
        ProjectCheck(
            "project item add refuse",
            ("project", "item", "add", "--issue", "42"),
            kind="refuse",
            needle="Refusing write",
            failure="refuse_gate",
        ),
        ProjectCheck(
            "project deploy refuse",
            ("project", "deploy"),
            kind="refuse",
            needle="Refusing write",
            failure="refuse_gate",
        ),
        ProjectCheck(
            "project ingest",
            ("project", "--format", "json", "ingest"),
            needle="updated",
        ),
        ProjectCheck(
            "project sync refuse",
            ("project", "sync"),
            kind="refuse",
            needle="Refusing write",
            failure="refuse_gate",
        ),
        ProjectCheck(
            "project sync",
            ("project", "--format", "json", "sync", "--yes"),
            needle="ingest",
        ),
    ]


def _path_for_check(check: ProjectCheck) -> tuple[str, ...]:
    return command_tokens(check.args)


def project_paths_with_ok_check() -> set[tuple[str, ...]]:
    out: set[tuple[str, ...]] = set()
    for check in project_checks():
        if check.kind != "ok" or check.failure:
            continue
        out.add(_path_for_check(check))
    return out


def project_paths_with_failure_check() -> set[tuple[str, ...]]:
    out: set[tuple[str, ...]] = set()
    for check in project_checks():
        if check.kind == "ok" and not check.failure:
            continue
        out.add(_path_for_check(check))
    return out


def assert_project_registry_complete() -> None:
    for path in PROJECT_COMMAND_PATHS:
        if not any(_path_for_check(c) == path for c in project_checks()):
            raise AssertionError(f"missing project integration check for path: {path}")


PROJECT_FAIL_EXEMPT_PATHS: frozenset[tuple[str, ...]] = frozenset({
    ("project", "list"),
    ("project", "pairs", "status"),
    ("project", "ingest"),
})


def assert_every_project_path_has_ok_and_failure_check() -> None:
    assert_project_registry_complete()
    for path in PROJECT_COMMAND_PATHS:
        has_ok = path in project_paths_with_ok_check()
        has_fail = path in project_paths_with_failure_check()
        if not has_ok:
            raise AssertionError(f"project {' '.join(path)} missing ok check")
        if path in PROJECT_FAIL_EXEMPT_PATHS:
            continue
        if not has_fail:
            raise AssertionError(f"project {' '.join(path)} missing fail check")


def run_project_check(check: ProjectCheck, *, repo_root: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.pop("CLI_GIT_ROOT", None)
    prev = os.getcwd()
    try:
        os.chdir(repo_root)
        with patch("src.commands.project._svc", lambda repo=None: _FakeProjectService()):
            result = _CLI_RUNNER.invoke(app, list(check.args), env=env)
    finally:
        os.chdir(prev)
    output = result.stdout + (result.stderr or "")
    if result.exception is not None:
        output += f"\n{result.exception}"
    return result.exit_code, output


def run_all_project_checks(repo_root: Path) -> list[str]:
    assert_every_project_path_has_ok_and_failure_check()
    errors: list[str] = []
    for check in project_checks():
        code, output = run_project_check(check, repo_root=repo_root)
        if check.kind == "ok":
            if code != 0:
                errors.append(f"{check.label}: exit {code}\n{output}")
                continue
        elif code == 0:
            errors.append(f"{check.label}: expected refusal, got exit 0\n{output}")
            continue
        if check.needle and check.needle not in output:
            if check.kind == "ok" and check.label == "project spawn dry-run":
                try:
                    payload = json.loads(output)
                    if payload.get("dry_run") is True:
                        continue
                except json.JSONDecodeError:
                    pass
            errors.append(f"{check.label}: missing needle {check.needle!r}\n{output}")
    return errors
