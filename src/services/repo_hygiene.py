"""Repository hygiene checks for app repos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_WORKFLOWS = {".github/workflows/pull-request.yml"}
EXEMPT_LAYOUT_REPOS = {"github-pipelines", "computer-science"}
STANDARD_ROOT_DIRS = frozenset({"src", "docs", "tests", "test", ".github"})
STANDARD_ROOT_FILES = frozenset({"README.md", "LICENSE", "CONTRIBUTING.md"})
ORCHESTRATION_PREFIXES = (
    ".github/actions/",
    "docker/",
    ".cli/",
)
PYTHON_CLI_ORCHESTRATION_PREFIXES = (
    ".github/actions/",
    "docker/",
)
APP_SCRIPT_PREFIXES = ("scripts/",)
PYTHON_CLI_FORBIDDEN_SCRIPT_PREFIXES = (
    "scripts/docker/",
    "scripts/test/",
    "scripts/deploy/",
    "scripts/release/",
)
DEFAULT_IGNORED_PREFIXES = (
    ".git/",
    ".venv/",
    "node_modules/",
    "__pycache__/",
    ".pytest_cache/",
    "dist/",
    "build/",
)


@dataclass(frozen=True)
class HygienePolicy:
    """Allowlist for repository file languages and metadata files."""

    allowed_extensions: frozenset[str] = frozenset()
    allowed_filenames: frozenset[str] = frozenset()
    allowed_paths: frozenset[str] = frozenset()
    allowed_root_dirs: frozenset[str] = frozenset()
    allowed_root_files: frozenset[str] = frozenset()
    max_depth: int | None = None
    ignored_prefixes: tuple[str, ...] = DEFAULT_IGNORED_PREFIXES
    ignored_paths: frozenset[str] = frozenset()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "HygienePolicy":
        allowed_extensions = frozenset(_normalize_extension(ext) for ext in _as_strings(data, "allowed_extensions"))
        allowed_filenames = frozenset(_as_strings(data, "allowed_filenames"))
        allowed_paths = frozenset(_normalize_path(path) for path in _as_strings(data, "allowed_paths"))
        allowed_root_dirs = frozenset(_as_strings(data, "allowed_root_dirs"))
        allowed_root_files = frozenset(_as_strings(data, "allowed_root_files"))
        max_depth_raw = data.get("max_depth")
        max_depth = None if max_depth_raw is None else int(max_depth_raw)
        if max_depth is not None and max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        ignored_prefixes = tuple(
            _normalize_prefix(prefix)
            for prefix in (*DEFAULT_IGNORED_PREFIXES, *_as_strings(data, "ignored_prefixes"))
        )
        ignored_paths = frozenset(_normalize_path(path) for path in _as_strings(data, "ignored_paths"))
        return cls(
            allowed_extensions=allowed_extensions,
            allowed_filenames=allowed_filenames,
            allowed_paths=allowed_paths,
            allowed_root_dirs=allowed_root_dirs,
            allowed_root_files=allowed_root_files,
            max_depth=max_depth,
            ignored_prefixes=ignored_prefixes,
            ignored_paths=ignored_paths,
        )

    def ignores(self, rel: str) -> bool:
        return rel in self.ignored_paths or any(rel.startswith(prefix) for prefix in self.ignored_prefixes)

    def allows(self, path: Path, rel: str) -> bool:
        if rel in self.allowed_paths or path.name in self.allowed_filenames:
            return True
        return path.suffix.lower() in self.allowed_extensions


def _as_strings(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


def _normalize_extension(value: str) -> str:
    ext = value.strip().lower()
    if not ext:
        raise ValueError("allowed_extensions cannot contain an empty value")
    return ext if ext.startswith(".") else f".{ext}"


def _normalize_path(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("/")


def _normalize_prefix(value: str) -> str:
    prefix = _normalize_path(value)
    return prefix if prefix.endswith("/") else f"{prefix}/"


def load_hygiene_policy(path: Path) -> HygienePolicy:
    with path.expanduser().open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("hygiene policy must be a mapping")
    return HygienePolicy.from_mapping(data)


def _forbidden_prefixes(root_name: str) -> tuple[str, ...]:
    if root_name == "github-pipelines":
        return ()
    if root_name == "python-cli":
        return (*PYTHON_CLI_ORCHESTRATION_PREFIXES, *PYTHON_CLI_FORBIDDEN_SCRIPT_PREFIXES)
    if root_name == "database":
        return ORCHESTRATION_PREFIXES
    return (*ORCHESTRATION_PREFIXES, *APP_SCRIPT_PREFIXES)


def _path_depth(rel: str) -> int:
    return len(Path(rel).parts)


def _check_structure(
    root: Path,
    *,
    require_layout: bool,
    policy: HygienePolicy | None,
) -> list[str]:
    errors: list[str] = []
    max_depth = policy.max_depth if policy else None
    root_dirs = policy.allowed_root_dirs if policy and policy.allowed_root_dirs else STANDARD_ROOT_DIRS
    root_files = policy.allowed_root_files if policy and policy.allowed_root_files else STANDARD_ROOT_FILES

    enforce_root_allowlist = bool(policy and (policy.allowed_root_dirs or policy.allowed_root_files))
    if require_layout and (root.name not in EXEMPT_LAYOUT_REPOS or enforce_root_allowlist):
        for entry in sorted(root.iterdir(), key=lambda path: path.name):
            if entry.name in {".git", ".venv", "node_modules", "__pycache__"}:
                continue
            if entry.is_dir():
                if entry.name not in root_dirs:
                    errors.append(f"unexpected root directory: {entry.name}/")
            elif entry.is_file() and entry.name not in root_files:
                if policy is None or not policy.allows(entry, entry.name):
                    errors.append(f"unexpected root file: {entry.name}")

    if max_depth is None:
        return errors

    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        if policy and policy.ignores(rel):
            continue
        if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in path.parts):
            continue
        depth = _path_depth(rel)
        if depth > max_depth:
            errors.append(f"directory exceeds max depth {max_depth}: {rel}/")
    return errors


def check_repo_hygiene(
    root: Path,
    *,
    require_layout: bool = False,
    require_structure: bool = False,
    policy: HygienePolicy | None = None,
) -> list[str]:
    root = root.expanduser().resolve()
    errors: list[str] = []
    forbidden_prefixes = _forbidden_prefixes(root.name)

    for path in root.rglob("*"):
        if any(part in {".git", "__pycache__"} for part in path.parts) or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if policy and policy.ignores(rel):
            continue
        if root.name != "github-pipelines" and rel.startswith(".github/workflows/") and rel not in ALLOWED_WORKFLOWS:
            errors.append(f"workflow belongs in github-pipelines: {rel}")
        elif rel == "Dockerfile" or any(rel.startswith(prefix) for prefix in forbidden_prefixes):
            errors.append(f"orchestration/script artifact belongs in python-cli or github-pipelines: {rel}")
        if policy and not policy.allows(path, rel):
            errors.append(f"file type is not allowed by hygiene policy: {rel}")

    if require_layout and root.name not in EXEMPT_LAYOUT_REPOS:
        if not (root / "README.md").is_file():
            errors.append("missing required file: README.md")
        for dirname in ("src", "docs"):
            if not (root / dirname).is_dir():
                errors.append(f"missing required directory: {dirname}/")
        if not (root / "test").is_dir() and not (root / "tests").is_dir():
            errors.append("missing required test directory: test/ or tests/")

    if require_structure or (policy and policy.max_depth is not None):
        errors.extend(_check_structure(root, require_layout=require_layout or require_structure, policy=policy))
    return errors
