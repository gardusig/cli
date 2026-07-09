"""Tests for profile README repo sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.gh_repo_readme import (
    END_MARKER,
    START_MARKER,
    format_repo_lines,
    patch_readme,
)


def test_format_repo_lines_includes_description() -> None:
    lines = format_repo_lines(
        "gardusig",
        [{"name": "python-cli", "url": "https://github.com/gardusig/cli", "description": "CLI"}],
    )
    assert lines == "- [python-cli](https://github.com/gardusig/cli) — CLI"


def test_patch_readme_replaces_marked_section(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Profile\n\n"
        f"{START_MARKER}\n-old-\n{END_MARKER}\n",
        encoding="utf-8",
    )
    updated = patch_readme(
        readme,
        "gardusig",
        [{"name": "database", "url": "https://github.com/gardusig/private", "description": ""}],
    )
    assert "- [database](https://github.com/gardusig/private)" in updated
    assert "-old-" not in updated


def test_patch_readme_requires_markers(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# no markers\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sync markers"):
        patch_readme(readme, "gardusig", [])
