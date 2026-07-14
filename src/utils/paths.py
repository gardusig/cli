"""Install layout and working-directory roots for the shipped CLI package."""

from __future__ import annotations

import os
from pathlib import Path


def install_root() -> Path:
    """Root of the installed ``src`` package (bundled defaults live under ``data/``)."""
    return Path(__file__).resolve().parents[1]


def bundled_path(*parts: str) -> Path:
    """Path to a file shipped inside ``src/data/``."""
    return install_root() / "data" / Path(*parts)


def bundled_config_dir() -> Path:
    """Packaged config templates (not the repo ``config/`` tree)."""
    return bundled_path("config")


def project_root() -> Path:
    """Current project directory (git checkout), never the install location."""
    override = os.environ.get("CLI_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").exists():
            return candidate
    return cwd


def resolve_repo_relative(path: Path | str, *, base: Path | None = None) -> Path:
    """Resolve *path* relative to *base* (default: :func:`project_root`)."""
    raw = Path(path).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    if base is None:
        from src.utils.config import project_root as _project_root

        base = _project_root()
    return base / raw
