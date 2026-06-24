"""Build and publish gardusig-cli distributions to PyPI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from cli.utils.config import project_root

DEFAULT_REPOSITORY_URL = "https://upload.pypi.org/legacy/"
TEST_REPOSITORY_URL = "https://test.pypi.org/legacy/"


class PyPiPublishError(RuntimeError):
    """PyPI build or upload failed."""


def resolve_pypi_token() -> str:
    token = os.environ.get("PYPI_API_TOKEN", "").strip()
    if not token:
        raise PyPiPublishError(
            "PYPI_API_TOKEN is not set. Add it to .env or export it before publishing.\n"
            "Create a token: https://pypi.org/manage/account/token/"
        )
    return token


def build_distributions(
    root: Path | None = None,
    *,
    output_dir: Path | None = None,
) -> list[Path]:
    """Build sdist + wheel via ``python -m build``."""
    root = (root or project_root()).resolve()
    out = output_dir or root / "dist"
    out.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(out)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "build failed").strip()
        raise PyPiPublishError(msg)
    artifacts = sorted(out.glob("*.whl")) + sorted(out.glob("*.tar.gz"))
    if not artifacts:
        raise PyPiPublishError(f"no artifacts in {out}")
    return artifacts


def publish_distributions(
    artifacts: list[Path],
    *,
    token: str,
    repository_url: str = DEFAULT_REPOSITORY_URL,
) -> list[str]:
    """Upload built artifacts with twine (``__token__`` / API token)."""
    if not artifacts:
        raise PyPiPublishError("no artifacts to upload")
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--repository-url",
        repository_url,
        *[str(path) for path in artifacts],
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "twine upload failed").strip()
        raise PyPiPublishError(msg)
    return [path.name for path in artifacts]
