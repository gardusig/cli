"""Public endpoint registry basics (integration execution is smoke-script only)."""

from __future__ import annotations

from pathlib import Path

from src.integration.public_endpoints import TOP_LEVEL_COMMANDS


def test_top_level_commands_include_gh() -> None:
    assert "gh" in TOP_LEVEL_COMMANDS


def test_integration_smoke_script_present() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "scripts" / "pull-request" / "integration-smoke.sh").is_file()
