"""Docker integration checks use mocked runner (registry gate removed)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

from src.integration.docker_integration import run_all_docker_checks


def test_mocked_docker_integration_passes() -> None:
    errors = run_all_docker_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
