"""Integration checks for cli contest commands (mocked Docker runner)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from typer.testing import CliRunner

from src.cli import app
from src.services.contest_runner import ContestValidateResult

_CLI_RUNNER = CliRunner()

CONTEST_SUBCOMMANDS = ("validate",)

CheckKind = Literal["ok", "refuse"]

TOY_FAST = "tests/fixtures/contest/toy/solution.cpp"
TOY_BRUTE = "tests/fixtures/contest/toy/brute.py"
TOY_GEN = "tests/fixtures/contest/toy/gen.py"


@dataclass(frozen=True)
class ContestCheck:
    label: str
    args: tuple[str, ...]
    kind: CheckKind = "ok"
    needle: str | None = None
    failure: str | None = None


def contest_checks() -> list[ContestCheck]:
    validate_args = (
        "contest",
        "validate",
        "--fast",
        TOY_FAST,
        "--brute",
        TOY_BRUTE,
        "--generator",
        TOY_GEN,
    )
    return [
        ContestCheck("contest validate pass", validate_args, needle="PASS"),
        ContestCheck(
            "contest validate fail",
            validate_args,
            kind="refuse",
            needle="FAIL",
            failure="validate_fail",
        ),
        ContestCheck(
            "contest validate missing paths",
            ("contest", "validate"),
            kind="refuse",
            needle="error",
            failure="missing_paths",
        ),
    ]


def contest_subcommands_with_ok_check() -> set[str]:
    ok: set[str] = set()
    for check in contest_checks():
        if check.kind != "ok" or check.failure:
            continue
        if len(check.args) >= 2 and check.args[0] == "contest":
            ok.add(check.args[1])
    return ok


def contest_subcommands_with_failure_check() -> set[str]:
    failed: set[str] = set()
    for check in contest_checks():
        if check.kind == "ok" and not check.failure:
            continue
        if len(check.args) >= 2 and check.args[0] == "contest":
            failed.add(check.args[1])
    return failed


def assert_contest_registry_complete() -> None:
    for sub in CONTEST_SUBCOMMANDS:
        if not any(
            c.args and len(c.args) >= 2 and c.args[0] == "contest" and c.args[1] == sub
            for c in contest_checks()
        ):
            raise AssertionError(f"missing contest integration check for: {sub}")


def assert_every_contest_subcommand_has_ok_check() -> None:
    missing = set(CONTEST_SUBCOMMANDS) - contest_subcommands_with_ok_check()
    if missing:
        raise AssertionError(f"contest subcommands without ok integration check: {sorted(missing)}")


def assert_every_contest_subcommand_has_failure_check() -> None:
    missing = set(CONTEST_SUBCOMMANDS) - contest_subcommands_with_failure_check()
    if missing:
        raise AssertionError(
            f"contest subcommands without failure integration check: {sorted(missing)}"
        )


def assert_every_contest_subcommand_has_ok_and_failure_check() -> None:
    assert_every_contest_subcommand_has_ok_check()
    assert_every_contest_subcommand_has_failure_check()


def run_contest_check(check: ContestCheck, *, repo_root: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.pop("CLI_GIT_ROOT", None)
    prev = os.getcwd()
    try:
        os.chdir(repo_root)
        result = _CLI_RUNNER.invoke(app, list(check.args), env=env)
    finally:
        os.chdir(prev)
    output = result.stdout + (result.stderr or "")
    if result.exception is not None:
        output += f"\n{result.exception}"
    return result.exit_code, output


def run_all_contest_checks(repo_root: Path) -> list[str]:
    assert_contest_registry_complete()
    assert_every_contest_subcommand_has_ok_and_failure_check()
    errors: list[str] = []
    for check in contest_checks():
        if check.failure == "missing_paths":
            code, output = run_contest_check(check, repo_root=repo_root)
        elif check.failure == "validate_fail":
            mock_result = ContestValidateResult(passed=False, error="small tier outputs differ")
            with patch("src.commands.contest.validate_contest", return_value=mock_result):
                code, output = run_contest_check(check, repo_root=repo_root)
        else:
            mock_result = ContestValidateResult(passed=True)
            with patch("src.commands.contest.validate_contest", return_value=mock_result):
                code, output = run_contest_check(check, repo_root=repo_root)

        if check.kind == "ok":
            if code != 0:
                errors.append(f"{check.label}: exit {code}\n{output}")
                continue
        else:
            if code == 0:
                errors.append(f"{check.label}: expected refusal, got exit 0\n{output}")
                continue
        if check.needle and check.needle not in output:
            errors.append(f"{check.label}: missing needle {check.needle!r}\n{output}")
    return errors
