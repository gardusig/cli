"""Unit-test registry gate: every public command has a mocked operation check."""

from __future__ import annotations

from src.integration.public_unit_runner import assert_public_unit_registry_complete


def test_public_unit_registry_covers_all_commands() -> None:
    assert_public_unit_registry_complete()
