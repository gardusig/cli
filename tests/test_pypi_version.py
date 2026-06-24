"""PyPI version helpers (pure logic; no subprocess)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gardusig_cli.services.pypi_publish import (
    PyPiPublishError,
    normalize_release_version,
    read_project_version,
    resolve_release_version,
    sync_version_files,
)


def test_normalize_release_version_strips_v() -> None:
    assert normalize_release_version("v1.0.0") == "1.0.0"
    assert normalize_release_version("1.0.0") == "1.0.0"


def test_normalize_release_version_rejects_invalid() -> None:
    with pytest.raises(PyPiPublishError, match="semver"):
        normalize_release_version("not-a-version")


def test_resolve_release_version_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_RELEASE_VERSION", "v2.3.4")
    assert resolve_release_version(None) == "2.3.4"


def test_sync_version_files_updates_pyproject_and_init(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "gardusig-cli"\nversion = "0.1.0"\n', encoding="utf-8")
    init_dir = tmp_path / "gardusig_cli"
    init_dir.mkdir()
    init_py = init_dir / "__init__.py"
    init_py.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    sync_version_files(tmp_path, "1.0.0")
    assert read_project_version(tmp_path) == "1.0.0"
    assert '__version__ = "1.0.0"' in init_py.read_text(encoding="utf-8")
