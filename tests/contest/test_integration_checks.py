"""Registry and mocked integration checks for cli contest commands."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

from gardusig_cli.integration.contest_integration import (
    CONTEST_SUBCOMMANDS,
    assert_every_contest_subcommand_has_ok_check,
    contest_checks,
    run_all_contest_checks,
)
from gardusig_cli.integration.integration_coverage import assert_integration_coverage_gate


def test_contest_subcommands_have_checks() -> None:
    assert_integration_coverage_gate()
    covered = {c.args[1] for c in contest_checks() if len(c.args) >= 2}
    assert set(CONTEST_SUBCOMMANDS) <= covered
    assert_every_contest_subcommand_has_ok_check()


def test_mocked_contest_integration_passes() -> None:
    errors = run_all_contest_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
