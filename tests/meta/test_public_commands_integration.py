"""Top-level CLI registration matches integration package registry."""

from __future__ import annotations

from pathlib import Path

from src.integration.public_endpoints import TOP_LEVEL_COMMANDS
from src.services.test_packages import assert_registry_covers_top_level_commands


def test_top_level_commands_match_test_package_registry() -> None:
    assert_registry_covers_top_level_commands()
    assert "gh" in TOP_LEVEL_COMMANDS


def test_integration_smoke_script_present() -> None:
    root = Path(__file__).resolve().parents[2]
    smoke = root / "scripts" / "pull-request" / "integration-smoke.sh"
    assert smoke.is_file()
