"""Docker-only guard for integration scratch directories."""

from __future__ import annotations

from tests.constants import ROOT

import pytest

from src.integration.docker_guard import (
    in_docker_integration,
    integration_scratch_dir,
    require_docker_integration,
)


def test_in_docker_integration_true_in_container() -> None:
    assert in_docker_integration() is True


def test_in_docker_integration_false_on_host(simulate_host_env: None) -> None:
    assert in_docker_integration() is False


def test_require_docker_integration_raises_on_host(simulate_host_env: None) -> None:
    with pytest.raises(RuntimeError, match="Docker"):
        require_docker_integration(context="unit test")


def test_integration_scratch_dir_requires_docker_on_host(simulate_host_env: None) -> None:
    with pytest.raises(RuntimeError, match="Docker"):
        integration_scratch_dir()
