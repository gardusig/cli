"""Chrome bookmark integration mocks."""

from __future__ import annotations

import os
from pathlib import Path


def chrome_bookmarks_env(workspace: Path, repo_root: Path) -> dict[str, str]:
    """Env for scripts/chrome/* against an isolated workspace."""
    bookmarks_file = workspace / "data" / "bookmarks" / "bookmarks.html"
    bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
    return {
        **os.environ,
        "CLI_ROOT": str(repo_root),
        "CLI_BOOKMARKS_FILE": str(bookmarks_file),
        "CLI_DOWNLOADS_DIR": str(workspace / "Downloads"),
        "CLI_SKIP_CHROME_AUTOMATION": "1",
    }
