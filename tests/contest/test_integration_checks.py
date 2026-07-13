"""Contest integration checks use mocked runner (registry gate removed)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

from src.integration.contest_integration import run_all_contest_checks


def test_mocked_contest_integration_passes() -> None:
    errors = run_all_contest_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
