"""Canonical inventory and gate for public CLI integration test coverage.

External callers (unit tests, ``tests/integration/check_integration_coverage.py``)
use this module to verify every public command has registered ok + fail integration
checks before the slower dockerized suites run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.integration.cli_api_checks import (
    ApiName,
    CliApiCheck,
    checks_for_path,
    cli_api_checks,
    command_path,
    registered_api_command_paths,
)
from src.integration.contest_integration import CONTEST_SUBCOMMANDS, ContestCheck, contest_checks
from src.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    DockerCheck,
    docker_checks,
)
from src.integration.public_endpoints import (
    GIT_SUBCOMMANDS,
    PYPI_SUBCOMMANDS,
    TOP_LEVEL_COMMANDS,
    EndpointCheck,
    endpoint_checks,
)
from src.integration.workspaces import API_WORKSPACES, fixture_dir

Category = Literal["api", "git", "pypi", "docker", "contest", "top"]

_API_NAMES: tuple[ApiName, ...] = ("notion", "drive", "chrome")

# Read-only commands with no meaningful CLI failure path (inventory still lists ok checks).
_FAIL_EXEMPT_PATHS: dict[Category, frozenset[tuple[str, ...]]] = {
    "git": frozenset({("git", "docs")}),
    "top": frozenset({("links",), ("restore",)}),
}

# Deferred/blocked commands with no success path (inventory still lists fail checks).
_OK_EXEMPT_API_PATHS: frozenset[tuple[str, ...]] = frozenset()


@dataclass(frozen=True)
class IntegrationCoverageRow:
    """One public CLI surface and its registered integration checks."""

    category: Category
    path: tuple[str, ...]
    ok_checks: tuple[str, ...]
    fail_checks: tuple[str, ...]
    fail_exempt: bool = False
    ok_exempt: bool = False

    @property
    def path_display(self) -> str:
        return " ".join(self.path)

    @property
    def complete(self) -> bool:
        if self.fail_exempt:
            return bool(self.ok_checks)
        if self.ok_exempt:
            return bool(self.fail_checks)
        return bool(self.ok_checks) and bool(self.fail_checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": list(self.path),
            "path_display": self.path_display,
            "ok_checks": list(self.ok_checks),
            "fail_checks": list(self.fail_checks),
            "fail_exempt": self.fail_exempt,
            "ok_exempt": self.ok_exempt,
            "complete": self.complete,
        }



def _api_cli_checks() -> list[CliApiCheck]:
    return cli_api_checks(drive_repo=".")


def _endpoint_success(check: EndpointCheck) -> bool:
    return check.kind == "ok" and 0 in check.accept_exit_codes


def _endpoint_failure(check: EndpointCheck) -> bool:
    return check.kind == "refuse" or check.failure is not None or (
        check.kind == "ok" and 0 not in check.accept_exit_codes
    )


def _docker_success(check: DockerCheck) -> bool:
    return check.kind == "ok"


def _docker_failure(check: DockerCheck) -> bool:
    return check.kind == "refuse" or check.failure is not None


def _contest_success(check: ContestCheck) -> bool:
    return check.kind == "ok" and not check.failure


def _contest_failure(check: ContestCheck) -> bool:
    return check.kind == "refuse" or check.failure is not None


def _labels_for_path(
    checks: list[CliApiCheck | EndpointCheck | DockerCheck | ContestCheck],
    path: tuple[str, ...],
    *,
    category: Category,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ok: list[str] = []
    fail: list[str] = []
    for check in checks:
        if category == "api":
            assert isinstance(check, CliApiCheck)
            if command_path(check.args)[: len(path)] != path:
                continue
            (ok if check.kind == "ok" else fail).append(check.label)
        elif category == "git":
            assert isinstance(check, EndpointCheck)
            if not check.args or check.args[0] != "git":
                continue
            check_path = tuple(check.args[: len(path)])
            if check_path != path:
                continue
            if _endpoint_success(check):
                ok.append(check.label)
            if _endpoint_failure(check):
                fail.append(check.label)
        elif category == "pypi":
            assert isinstance(check, EndpointCheck)
            if not check.args or check.args[0] != "pypi":
                continue
            from src.integration.public_endpoints import _pypi_command_path_from_check_args

            check_sub = _pypi_command_path_from_check_args(check.args)
            expected_sub = " ".join(path[1:]) if len(path) > 1 else None
            if check_sub != expected_sub:
                continue
            if _endpoint_success(check):
                ok.append(check.label)
            if _endpoint_failure(check):
                fail.append(check.label)
        elif category == "docker":
            assert isinstance(check, DockerCheck)
            if len(check.args) < 2 or check.args[0] != "docker" or check.args[1] != path[1]:
                continue
            if _docker_success(check):
                ok.append(check.label)
            if _docker_failure(check):
                fail.append(check.label)
        elif category == "contest":
            assert isinstance(check, ContestCheck)
            if len(check.args) < 2 or check.args[0] != "contest" or check.args[1] != path[1]:
                continue
            if _contest_success(check):
                ok.append(check.label)
            if _contest_failure(check):
                fail.append(check.label)
        elif category == "top":
            assert isinstance(check, EndpointCheck)
            if not check.args or check.args[0] != path[0]:
                continue
            if _endpoint_success(check):
                ok.append(check.label)
            if _endpoint_failure(check):
                fail.append(check.label)
    return tuple(ok), tuple(fail)


def _api_rows(checks: list[CliApiCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for api in _API_NAMES:
        for path in sorted(registered_api_command_paths(api)):
            matched = checks_for_path(checks, api=api, path=path)
            ok = tuple(c.label for c in matched if c.kind == "ok")
            fail = tuple(c.label for c in matched if c.kind == "fail")
            rows.append(
                IntegrationCoverageRow(
                    "api",
                    path,
                    ok,
                    fail,
                    ok_exempt=path in _OK_EXEMPT_API_PATHS,
                )
            )
    return rows


def _git_rows(checks: list[EndpointCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for sub in GIT_SUBCOMMANDS:
        path = ("git",) + tuple(sub.split())
        ok, fail = _labels_for_path(checks, path, category="git")
        rows.append(
            IntegrationCoverageRow(
                "git",
                path,
                ok,
                fail,
                fail_exempt=path in _FAIL_EXEMPT_PATHS["git"],
            )
        )
    return rows


def _pypi_rows(checks: list[EndpointCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for sub in PYPI_SUBCOMMANDS:
        path = ("pypi",) + tuple(sub.split())
        ok, fail = _labels_for_path(checks, path, category="pypi")
        rows.append(IntegrationCoverageRow("pypi", path, ok, fail))
    return rows


def _docker_rows(checks: list[DockerCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for sub in DOCKER_SUBCOMMANDS:
        path = ("docker", sub)
        ok, fail = _labels_for_path(checks, path, category="docker")
        rows.append(IntegrationCoverageRow("docker", path, ok, fail))
    return rows


def _contest_rows(checks: list[ContestCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for sub in CONTEST_SUBCOMMANDS:
        path = ("contest", sub)
        ok, fail = _labels_for_path(checks, path, category="contest")
        rows.append(IntegrationCoverageRow("contest", path, ok, fail))
    return rows


def _top_level_rows(checks: list[EndpointCheck]) -> list[IntegrationCoverageRow]:
    rows: list[IntegrationCoverageRow] = []
    for name in TOP_LEVEL_COMMANDS:
        if name in _API_NAMES or name in {"git", "docker", "contest", "pypi"}:
            continue
        path = (name,)
        ok, fail = _labels_for_path(checks, path, category="top")
        rows.append(
            IntegrationCoverageRow(
                "top",
                path,
                ok,
                fail,
                fail_exempt=path in _FAIL_EXEMPT_PATHS["top"],
            )
        )
    return rows


def integration_coverage_inventory() -> tuple[IntegrationCoverageRow, ...]:
    """Every public CLI command path with ok/fail integration check labels."""
    api_checks = _api_cli_checks()
    endpoints = endpoint_checks()
    docker = docker_checks()
    contest = contest_checks()
    rows = [
        *_api_rows(api_checks),
        *_git_rows(endpoints),
        *_pypi_rows(endpoints),
        *_docker_rows(docker),
        *_contest_rows(contest),
        *_top_level_rows(endpoints),
    ]
    return tuple(sorted(rows, key=lambda row: (row.category, row.path)))


def integration_coverage_summary() -> dict[str, Any]:
    rows = integration_coverage_inventory()
    complete = sum(1 for row in rows if row.complete)
    return {
        "total_commands": len(rows),
        "complete": complete,
        "incomplete": len(rows) - complete,
        "by_category": {
            category: {
                "total": sum(1 for row in rows if row.category == category),
                "complete": sum(
                    1 for row in rows if row.category == category and row.complete
                ),
            }
            for category in ("api", "git", "pypi", "docker", "contest", "top")
        },
    }


def integration_coverage_manifest() -> dict[str, Any]:
    """JSON-serializable inventory for external tooling and CI artifacts."""
    summary = integration_coverage_summary()
    return {
        "version": 1,
        "summary": summary,
        "commands": [row.as_dict() for row in integration_coverage_inventory()],
    }


def format_integration_coverage_report() -> str:
    lines = [
        "Integration coverage inventory (ok + fail checks per public command)",
        f"  total: {integration_coverage_summary()['total_commands']} commands",
        "",
    ]
    current: Category | None = None
    for row in integration_coverage_inventory():
        if row.category != current:
            current = row.category
            lines.append(f"[{current}]")
        status = "ok" if row.complete else "INCOMPLETE"
        exempt = " (fail exempt)" if row.fail_exempt else ""
        lines.append(f"  {status}  {row.path_display}{exempt}")
        if row.ok_checks:
            lines.append(f"        ok:   {', '.join(row.ok_checks)}")
        if row.fail_checks:
            lines.append(f"        fail: {', '.join(row.fail_checks)}")
        elif not row.fail_exempt:
            lines.append("        fail: (none)")
    return "\n".join(lines)


def assert_integration_coverage_gate() -> None:
    """Fail fast when any public command lacks required integration check pairs."""
    from src.integration.public_commands import assert_public_command_registry_complete

    assert_public_command_registry_complete()

    incomplete = [row for row in integration_coverage_inventory() if not row.complete]
    if not incomplete:
        return

    lines = [
        "Integration coverage gate failed — missing ok/fail integration checks:",
        "",
    ]
    for row in incomplete:
        missing: list[str] = []
        if not row.ok_checks and not row.ok_exempt:
            missing.append("ok")
        if not row.fail_checks and not row.fail_exempt:
            missing.append("fail")
        lines.append(
            f"  {' '.join(row.path)} ({row.category}): missing {', '.join(missing)}"
        )
        if row.ok_checks:
            lines.append(f"    ok:   {', '.join(row.ok_checks)}")
        if row.fail_checks:
            lines.append(f"    fail: {', '.join(row.fail_checks)}")
    raise AssertionError("\n".join(lines))


def manifest_json(*, indent: int = 2) -> str:
    return json.dumps(integration_coverage_manifest(), indent=indent)
