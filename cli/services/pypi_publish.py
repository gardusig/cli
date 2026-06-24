"""Build and publish gardusig-cli distributions to PyPI."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from cli.utils.config import project_root

DEFAULT_REPOSITORY_URL = "https://upload.pypi.org/legacy/"
TEST_REPOSITORY_URL = "https://test.pypi.org/legacy/"

_VERSION_LINE_RE = re.compile(r'^(version\s*=\s*")[^"]+(")\s*$', re.MULTILINE)
_INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"[^"]+"\s*$', re.MULTILINE)


class PyPiPublishError(RuntimeError):
    """PyPI build or upload failed."""


def normalize_release_version(raw: str) -> str:
    """Strip optional ``v`` prefix from a git tag or version string."""
    value = raw.strip()
    if value.startswith("v"):
        value = value[1:]
    if not value:
        raise PyPiPublishError(f"invalid release version: {raw!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+([-.][0-9A-Za-z.]+)?", value):
        raise PyPiPublishError(
            f"release version must look like semver (got {value!r}); use tags like v1.0.0"
        )
    return value


def read_project_version(root: Path | None = None) -> str:
    root = (root or project_root()).resolve()
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = _VERSION_LINE_RE.search(text)
    if not match:
        raise PyPiPublishError("version not found in pyproject.toml")
    full = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not full:
        raise PyPiPublishError("version not found in pyproject.toml")
    return full.group(1)


def resolve_release_version(
    explicit: str | None = None,
    *,
    root: Path | None = None,
) -> str | None:
    """Version from CLI flag, CLI_RELEASE_VERSION env, or None (keep pyproject)."""
    if explicit and explicit.strip():
        return normalize_release_version(explicit)
    env = os.environ.get("CLI_RELEASE_VERSION", "").strip()
    if env:
        return normalize_release_version(env)
    return None


def sync_version_files(root: Path | None, version: str) -> None:
    """Write ``version`` to pyproject.toml and cli/__init__.py before a release build."""
    root = (root or project_root()).resolve()
    version = normalize_release_version(version)
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    new_text, count = _VERSION_LINE_RE.subn(rf"\g<1>{version}\g<2>", text, count=1)
    if count != 1:
        raise PyPiPublishError("failed to update version in pyproject.toml")
    pyproject.write_text(new_text, encoding="utf-8")

    init_py = root / "cli" / "__init__.py"
    init_text = init_py.read_text(encoding="utf-8")
    new_init, init_count = _INIT_VERSION_RE.subn(
        f'__version__ = "{version}"',
        init_text,
        count=1,
    )
    if init_count != 1:
        raise PyPiPublishError("failed to update __version__ in cli/__init__.py")
    init_py.write_text(new_init, encoding="utf-8")


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
    version: str | None = None,
) -> list[Path]:
    """Build sdist + wheel via ``python -m build``."""
    root = (root or project_root()).resolve()
    release_version = resolve_release_version(version, root=root)
    if release_version:
        sync_version_files(root, release_version)
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
    if release_version:
        for artifact in artifacts:
            if release_version not in artifact.name:
                raise PyPiPublishError(
                    f"artifact {artifact.name} does not include release version {release_version}"
                )
    return artifacts


def publish_distributions(
    artifacts: list[Path],
    *,
    token: str,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    skip_existing: bool = False,
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
    ]
    if skip_existing:
        cmd.append("--skip-existing")
    cmd.extend(str(path) for path in artifacts)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "twine upload failed").strip()
        raise PyPiPublishError(msg)
    return [path.name for path in artifacts]
