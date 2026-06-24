"""PyPI package metadata vs repo naming."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def _project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def test_pypi_distribution_name_is_gardusig_cli() -> None:
    assert _project()["name"] == "gardusig-cli"


def test_pypi_urls_point_at_cli_repo() -> None:
    urls = _project()["urls"]
    assert urls["Repository"] == "https://github.com/gardusig/cli"
    assert urls["Homepage"] == "https://github.com/gardusig/cli"
    assert urls["Issues"] == "https://github.com/gardusig/cli/issues"


def test_console_entrypoint_stays_cli() -> None:
    assert _project()["scripts"]["cli"] == "gardusig_cli.cli:run"
