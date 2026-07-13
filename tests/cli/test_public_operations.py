"""Parametrized unit tests for every public CLI endpoint (externals mocked)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.constants import ROOT
from src.integration.public_endpoints import endpoint_checks
from src.integration.public_unit_runner import prepare_unit_git_roots, run_unit_endpoint_check
from src.services.git_shortcuts import GitShortcuts


@pytest.fixture(autouse=True)
def _isolate_host_git_tags():
    """Avoid host repo tags affecting tag policy in endpoint unit tests."""
    with (
        patch.object(GitShortcuts, "all_tag_names", return_value=[]),
        patch.object(GitShortcuts, "list_local_tags", return_value=[]),
        patch.object(GitShortcuts, "list_remote_tags", return_value=[]),
    ):
        yield


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "endpoint_check" in metafunc.fixturenames:
        checks = endpoint_checks()
        metafunc.parametrize("endpoint_check", checks, ids=[check.label for check in checks])


@pytest.fixture
def unit_git_roots(tmp_path):
    return prepare_unit_git_roots(tmp_path)


def test_public_endpoint_operation(endpoint_check, unit_git_roots) -> None:
    git_root, outside = unit_git_roots
    errors = run_unit_endpoint_check(
        endpoint_check,
        repo_root=ROOT,
        git_root=git_root,
        outside_git_root=outside,
    )
    assert not errors, "\n".join(errors)
