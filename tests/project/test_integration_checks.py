"""Registry and mocked integration checks for top-level cli project commands."""

from __future__ import annotations

from tests.constants import ROOT

from src.integration.integration_coverage import assert_integration_coverage_gate
from src.integration.project_integration import (
    PROJECT_COMMAND_PATHS,
    assert_every_project_path_has_ok_and_failure_check,
    project_checks,
    run_all_project_checks,
)
from src.integration.cli_api_checks import command_tokens


def test_project_paths_have_checks() -> None:
    assert_integration_coverage_gate()
    covered = [command_tokens(c.args) for c in project_checks()]
    for path in PROJECT_COMMAND_PATHS:
        assert any(
            len(tokens) >= len(path) and tokens[: len(path)] == path for tokens in covered
        ), f"missing check for {' '.join(path)}"
    assert_every_project_path_has_ok_and_failure_check()


def test_mocked_project_integration_passes() -> None:
    errors = run_all_project_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
