"""Validate stable selective-CI contract payloads."""

from __future__ import annotations

from src.services.test_packages import (
    full_suite_payload,
    package_command_payload,
    package_resolution_payload,
    pipeline_contract,
)


def test_pipeline_contract_has_stable_keys() -> None:
    contract = pipeline_contract()
    assert contract["owner"] == "gardusig/github-pipelines"
    assert "resolve_paths" in contract["repo_local_commands"]
    assert "run_package" in contract["repo_local_commands"]
    assert "full_suite" in contract["repo_local_commands"]
    assert contract["stable_check_names"] == [
        "selective-plan",
        "unit-package",
        "integration-package",
        "pypi-package",
        "full-suite",
    ]


def test_resolve_payload_shape() -> None:
    payload = package_resolution_payload(["src/commands/gh.py"])
    for key in (
        "changed_paths",
        "package_names",
        "unit_test_paths",
        "integration_checks",
        "full_suite",
        "pipeline_contract",
    ):
        assert key in payload
    assert "gh" in payload["package_names"]
    assert payload["full_suite"] is False


def test_run_payload_uses_package_integration_for_gh() -> None:
    payload = package_command_payload("gh", include_unit=False)
    commands = [" ".join(command["command"]) for command in payload["commands"]]
    assert any("check_package_integration.py --package gh" in row for row in commands)


def test_suite_payload_includes_live_docker() -> None:
    payload = full_suite_payload()
    assert "live_commands" in payload
    assert any("check_docker_commands.py --live" in " ".join(cmd["command"]) for cmd in payload["live_commands"])
    assert payload["pipeline_contract"]["owner"] == "gardusig/github-pipelines"
