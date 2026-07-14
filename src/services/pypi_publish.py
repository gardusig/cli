"""Build and publish gardusig-cli distributions to PyPI."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.utils.config import project_root

DEFAULT_REPOSITORY_URL = "https://upload.pypi.org/legacy/"
TEST_REPOSITORY_URL = "https://test.pypi.org/legacy/"
PACKAGE_NAME = "gardusig-cli"
DEFAULT_FIRST_RELEASE_VERSION = "0.1.0"

_VERSION_LINE_RE = re.compile(r'^(version\s*=\s*")[^"]+(")\s*$', re.MULTILINE)
_INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"[^"]+"\s*$', re.MULTILINE)
_RELEASE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+([-.][0-9A-Za-z.]+)?$")  # legacy tests


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


def validate_release_tag_name(raw: str) -> str:
    """Require PyPI-style annotated tag names: ``vX.Y.Z`` (``v`` prefix mandatory)."""
    from src.services.tag_policy import TagPattern, TagPolicy, validate_tag_name

    return validate_tag_name(raw, TagPolicy(pattern=TagPattern.SEMVER_V))


def format_release_tag(version: str) -> str:
    """Build ``vX.Y.Z`` from a version or tag string."""
    return f"v{normalize_release_version(version)}"


def default_release_tag_name(root: Path | None = None) -> str:
    """Default git tag name from ``pyproject.toml`` in *root* (``v{version}``)."""
    return format_release_tag(read_project_version(root))


def read_version_at_git_ref(ref: str, root: Path | None = None) -> str:
    """Read ``version`` from ``pyproject.toml`` at a git *ref*."""
    root = (root or project_root()).resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:pyproject.toml"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PyPiPublishError(f"cannot read pyproject.toml at {ref!r}")
    match = re.search(r'version\s*=\s*"([^"]+)"', result.stdout)
    if not match:
        raise PyPiPublishError(f"version not found in pyproject.toml at {ref!r}")
    return match.group(1)


def read_init_version(root: Path | None = None) -> str:
    root = (root or project_root()).resolve()
    init_py = root / "src" / "__init__.py"
    if not init_py.is_file():
        raise PyPiPublishError("__init__.py not found")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_py.read_text(encoding="utf-8"))
    if not match:
        raise PyPiPublishError("__version__ not found in src/__init__.py")
    return match.group(1)


def assert_versions_in_sync(root: Path | None = None) -> None:
    root = (root or project_root()).resolve()
    pyproject_v = read_project_version(root)
    try:
        init_v = read_init_version(root)
    except PyPiPublishError:
        return
    if pyproject_v != init_v:
        raise PyPiPublishError(
            f"version mismatch: pyproject.toml has {pyproject_v!r}, "
            f"src/__init__.py has {init_v!r}"
        )


def assert_version_increased_vs_ref(
    base_ref: str,
    *,
    root: Path | None = None,
) -> str:
    """Ensure working-tree version is strictly greater than *base_ref*."""
    from src.services.tag_policy import bump_semver, compare_versions

    root = (root or project_root()).resolve()
    assert_versions_in_sync(root)
    base_v = read_version_at_git_ref(base_ref, root)
    head_v = read_project_version(root)
    if compare_versions(head_v, base_v) <= 0:
        suggested = bump_semver(base_v, level="patch")
        raise PyPiPublishError(
            f"version {head_v!r} on this branch is not greater than {base_ref} ({base_v!r}). "
            f"Bump pyproject.toml and src/__init__.py to at least {suggested!r}."
        )
    return head_v


def assert_version_increased_vs_version(
    base_version: str,
    *,
    root: Path | None = None,
) -> str:
    """Ensure working-tree version is strictly greater than *base_version*."""
    from src.services.tag_policy import bump_semver, compare_versions

    root = (root or project_root()).resolve()
    assert_versions_in_sync(root)
    base_v = normalize_release_version(base_version)
    head_v = read_project_version(root)
    if compare_versions(head_v, base_v) <= 0:
        suggested = bump_semver(base_v, level="patch")
        raise PyPiPublishError(
            f"version {head_v!r} on this branch is not greater than {base_v!r}. "
            f"Bump pyproject.toml and src/__init__.py to at least {suggested!r}."
        )
    return head_v


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


def fetch_latest_published_version(
    package: str = PACKAGE_NAME,
    *,
    testpypi: bool = False,
    timeout: float = 20.0,
) -> str | None:
    """Return the highest semver published on PyPI (or TestPyPI), or ``None`` when absent."""
    from src.services.tag_policy import compare_versions

    url = package_index_json_url(package, testpypi=testpypi)
    label = "TestPyPI" if testpypi else "PyPI"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise PyPiPublishError(f"{label} index HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise PyPiPublishError(f"{label} index unreachable: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise PyPiPublishError(f"invalid JSON from {label} index ({url})") from exc

    releases = data.get("releases") or {}
    versions = [version for version, files in releases.items() if files]
    if not versions:
        return None

    best: str | None = None
    for candidate in versions:
        try:
            normalized = normalize_release_version(candidate)
        except PyPiPublishError:
            continue
        if best is None:
            best = normalized
            continue
        if compare_versions(normalized, best) > 0:
            best = normalized
    return best


def fetch_greatest_published_version(
    package: str = PACKAGE_NAME,
    *,
    timeout: float = 20.0,
) -> str | None:
    """Return the highest semver published on PyPI or TestPyPI, or ``None`` when absent."""
    from src.services.tag_policy import compare_versions

    best: str | None = None
    errors: list[str] = []
    for testpypi in (False, True):
        label = "TestPyPI" if testpypi else "PyPI"
        try:
            candidate = fetch_latest_published_version(
                package,
                testpypi=testpypi,
                timeout=timeout,
            )
        except PyPiPublishError as exc:
            errors.append(f"{label}: {exc}")
            continue
        if candidate is None:
            continue
        if best is None or compare_versions(candidate, best) > 0:
            best = candidate
    if best is not None:
        return best
    if errors:
        raise PyPiPublishError("; ".join(errors))
    return None


def suggest_next_release_version(
    *,
    published: str | None = None,
    level: str = "patch",
    first_default: str = DEFAULT_FIRST_RELEASE_VERSION,
    root: Path | None = None,
) -> str:
    """Next PyPI-compatible version: patch bump over *published*, else first-release default."""
    from src.services.tag_policy import bump_semver

    root = (root or project_root()).resolve()
    if published is None:
        published = fetch_greatest_published_version()

    if published:
        return bump_semver(normalize_release_version(published), level=level)

    try:
        return normalize_release_version(read_project_version(root))
    except (PyPiPublishError, OSError):
        return normalize_release_version(first_default)


def apply_next_release_version(
    *,
    published: str | None = None,
    level: str = "patch",
    first_default: str = DEFAULT_FIRST_RELEASE_VERSION,
    root: Path | None = None,
) -> str:
    """Write the suggested next version to ``pyproject.toml`` and ``src/__init__.py``."""
    root = (root or project_root()).resolve()
    version = suggest_next_release_version(
        published=published,
        level=level,
        first_default=first_default,
        root=root,
    )
    sync_version_files(root, version)
    return version


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
    """Write ``version`` to pyproject.toml and src/__init__.py before a release build."""
    root = (root or project_root()).resolve()
    version = normalize_release_version(version)
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    new_text, count = _VERSION_LINE_RE.subn(rf"\g<1>{version}\g<2>", text, count=1)
    if count != 1:
        raise PyPiPublishError("failed to update version in pyproject.toml")
    pyproject.write_text(new_text, encoding="utf-8")

    init_py = root / "src" / "__init__.py"
    init_text = init_py.read_text(encoding="utf-8")
    new_init, init_count = _INIT_VERSION_RE.subn(
        f'__version__ = "{version}"',
        init_text,
        count=1,
    )
    if init_count != 1:
        raise PyPiPublishError("failed to update __version__ in src/__init__.py")
    init_py.write_text(new_init, encoding="utf-8")


def resolve_pypi_token() -> str:
    token = os.environ.get("PYPI_API_TOKEN", "").strip()
    if not token:
        raise PyPiPublishError(
            "PYPI_API_TOKEN is not set. Add it to .env or export it before publishing.\n"
            "Create a token: https://pypi.org/manage/account/token/"
        )
    return token


def resolve_testpypi_token() -> str:
    token = os.environ.get("TESTPYPI_API_TOKEN", "").strip() or os.environ.get("PYPI_API_TOKEN", "").strip()
    if not token:
        raise PyPiPublishError(
            "TESTPYPI_API_TOKEN is not set. Add it to CI secrets or export it before publishing to TestPyPI.\n"
            "Create a token: https://test.pypi.org/manage/account/token/"
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
        for meta in root.glob("*.egg-info"):
            if meta.is_dir():
                shutil.rmtree(meta)
    out = output_dir or root / "dist"
    out.mkdir(parents=True, exist_ok=True)
    if release_version:
        for old in out.iterdir():
            if old.is_file():
                old.unlink()
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


def package_index_json_url(package: str, *, testpypi: bool = False) -> str:
    """Public JSON metadata URL for a package (PyPI or TestPyPI)."""
    base = "https://test.pypi.org" if testpypi else "https://pypi.org"
    return f"{base}/pypi/{package}/json"


def verify_package_version_on_index(
    package: str,
    version: str,
    *,
    testpypi: bool = False,
    timeout: float = 15.0,
    retries: int = 12,
    retry_delay: float = 5.0,
) -> None:
    """Confirm ``version`` appears on the package project page (JSON API)."""
    version = normalize_release_version(version)
    url = package_index_json_url(package, testpypi=testpypi)
    label = "TestPyPI" if testpypi else "PyPI"
    last_error: str | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            releases = data.get("releases") or {}
            if version in releases and releases[version]:
                return
            latest = (data.get("info") or {}).get("version")
            if latest == version:
                return
            last_error = (
                f"{package}=={version} not listed on {label} ({url}); "
                f"releases={sorted(releases.keys())[-5:]}"
            )
        except urllib.error.HTTPError as exc:
            last_error = f"{label} index HTTP {exc.code} for {url}"
        except urllib.error.URLError as exc:
            last_error = f"{label} index unreachable: {exc.reason}"
        except json.JSONDecodeError:
            last_error = f"invalid JSON from {label} index ({url})"
        if attempt < retries:
            time.sleep(retry_delay)
    raise PyPiPublishError(last_error or f"failed to verify {package}=={version} on {label}")
