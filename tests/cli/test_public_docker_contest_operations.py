"""Parametrized unit tests for docker and contest CLI operations (externals mocked)."""

from __future__ import annotations

import pytest

from tests.constants import ROOT
from src.integration.contest_integration import contest_checks
from src.integration.docker_integration import docker_checks
from src.integration.public_unit_runner import run_unit_contest_check, run_unit_docker_check


@pytest.mark.parametrize("docker_check", docker_checks(), ids=lambda check: check.label)
def test_public_docker_operation(docker_check) -> None:
    errors = run_unit_docker_check(docker_check, repo_root=ROOT)
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("contest_check", contest_checks(), ids=lambda check: check.label)
def test_public_contest_operation(contest_check) -> None:
    errors = run_unit_contest_check(contest_check, repo_root=ROOT)
    assert not errors, "\n".join(errors)
