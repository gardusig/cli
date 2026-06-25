"""One integration test per public endpoint check (git, pypi, top-level, etc.)."""

from __future__ import annotations

import pytest

from src.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
from src.integration.git_mocks import patch_remote_git
from src.integration.public_endpoints import (
    EndpointCheck,
    endpoint_checks,
    execute_endpoint_integration_check,
    prepare_git_repo,
)
from tests.constants import ROOT


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "endpoint_check" not in metafunc.fixturenames:
        return
    checks = endpoint_checks()
    metafunc.parametrize(
        "endpoint_check",
        checks,
        ids=[check.label for check in checks],
    )


@pytest.mark.integration
def test_public_endpoint_check(endpoint_check: EndpointCheck) -> None:
    git_dir = integration_temp_dir("cli-endpoint-")
    outside = integration_temp_dir("cli-outside-")
    try:
        prepare_git_repo(git_dir)
        with patch_remote_git():
            errors = execute_endpoint_integration_check(
                endpoint_check,
                repo_root=ROOT,
                git_root=git_dir,
                outside_git_root=outside,
            )
        assert errors == [], "\n---\n".join(errors)
    finally:
        cleanup_integration_temp_dir(git_dir)
        cleanup_integration_temp_dir(outside)
