from __future__ import annotations

from tests.constants import ROOT

from src.integration.public_endpoints import TOP_LEVEL_COMMANDS
from src.services.test_packages import (
    assert_registry_covers_top_level_commands,
    full_suite_payload,
    normalize_changed_path,
    package_command_payload,
    package_names,
    package_resolution_payload,
    resolve_test_packages,
)


def test_registry_covers_public_top_level_commands() -> None:
    assert_registry_covers_top_level_commands()
    assert set(TOP_LEVEL_COMMANDS).issubset(package_names())


def test_resolve_git_command_path_to_git_package() -> None:
    packages = resolve_test_packages(["src/commands/git.py"])

    assert "git" in packages


def test_resolve_test_path_to_package() -> None:
    packages = resolve_test_packages(["tests/git/test_deploy.py"])

    assert "git" in packages


def test_absolute_paths_are_normalized() -> None:
    packages = resolve_test_packages([str(ROOT / "src" / "commands" / "git.py")])

    assert "git" in packages


def test_registry_paths_are_portable_repo_relative_paths() -> None:
    assert (
        normalize_changed_path("./src/services/test_packages.py")
        == "src/services/test_packages.py"
    )
    assert (
        normalize_changed_path("/tmp/other-checkout/src/commands/git.py")
        == "tmp/other-checkout/src/commands/git.py"
    )


def test_shared_cli_path_marks_broad_resolution() -> None:
    payload = package_resolution_payload(["src/cli.py"])

    assert "cli" in payload["package_names"]
    assert payload["broad"] is True
    assert payload["full_suite"] is True
    assert any("broad package" in reason for reason in payload["full_suite_reasons"])


def test_opencode_paths_are_marked_as_token_costing() -> None:
    payload = package_resolution_payload(["src/providers/opencode.py"])

    assert "opencode" in payload["package_names"]
    assert payload["requires_ai"] is True
    assert payload["costs_api_tokens"] is True
    assert any("paid AI commands" in line for line in payload["instructions"])


def test_package_command_payload_uses_registry_paths() -> None:
    payload = package_command_payload("git")

    assert payload["package"]["name"] == "git"
    assert any(command["kind"] == "unit" for command in payload["commands"])
    assert any("tests/git/" in command["command"] for command in payload["commands"])
    assert any(
        "check_package_integration.py" in " ".join(command["command"])
        for command in payload["commands"]
        if command["kind"] == "integration"
    )
    assert payload["pipeline_contract"]["owner"] == "gardusig/cli"


def test_full_suite_payload_includes_core_and_package_commands() -> None:
    payload = full_suite_payload()

    assert "git" in payload["packages"]
    assert any(command["kind"] == "core" for command in payload["core_commands"])
    assert any(command["package"] == "git" for command in payload["commands"])
    assert any(command["kind"] == "live" for command in payload["commands"])
    assert payload["pipeline_contract"]["owner"] == "gardusig/cli"


def test_many_packages_fall_back_to_full_suite() -> None:
    payload = package_resolution_payload(
        [
            "src/commands/git.py",
            "src/commands/chrome.py",
            "src/commands/notion.py",
        ],
        package_limit=2,
    )

    assert payload["full_suite"] is True
    assert any("exceeds limit" in reason for reason in payload["full_suite_reasons"])
