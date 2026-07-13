"""Repository hygiene checks for app repos."""

from __future__ import annotations

from dataclasses import dataclass, replace
import fnmatch
from pathlib import Path
import re
from typing import Any

import yaml

from src.services.toolkit.detect import repo_slug

ALLOWED_WORKFLOWS = {
    ".github/workflows/pull-request.yaml",
    ".github/workflows/release.yaml",
}
PIPELINE_WORKFLOW_CONFIGS: set[str] = set()
EXEMPT_LAYOUT_REPOS = {"github-pipelines"}
STANDARD_ROOT_DIRS = frozenset({"src", "docs", "tests", "test", ".github"})
STANDARD_ROOT_FILES = frozenset({"README.md", "LICENSE", "CONTRIBUTING.md"})
ORCHESTRATION_PREFIXES = (
    ".github/actions/",
    ".cli/",
)
PYTHON_CLI_ORCHESTRATION_PREFIXES = (
    ".github/actions/",
)
APP_SCRIPT_PREFIXES: tuple[str, ...] = ()
CLI_REFERENCE_RE = re.compile(r"(^|[\s`\"'])cli(\s|$)|gardusig-cli")
PYTHON_CLI_FORBIDDEN_SCRIPT_PREFIXES: tuple[str, ...] = ()
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
    forbidden_extensions: frozenset[str] = frozenset()
    forbidden_paths: frozenset[str] = frozenset()
    forbidden_globs: tuple[str, ...] = ()
    forbidden_messages: dict[str, str] | None = None
    forbid_direct_cli_references: bool = False
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
        forbidden_extensions = frozenset(_normalize_extension(ext) for ext in _as_strings(data, "forbidden_extensions"))
        forbidden_paths = frozenset(_normalize_path(path) for path in _as_strings(data, "forbidden_paths"))
        forbidden_globs = tuple(_normalize_path(path) for path in _as_strings(data, "forbidden_globs"))
        forbidden_messages_raw = data.get("forbidden_messages") or {}
        if not isinstance(forbidden_messages_raw, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in forbidden_messages_raw.items()
        ):
            raise ValueError("forbidden_messages must be a mapping of strings")
        forbidden_messages = {str(key): str(value) for key, value in forbidden_messages_raw.items()}
        forbid_direct_cli_references = bool(data.get("forbid_direct_cli_references", False))
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
            forbidden_extensions=forbidden_extensions,
            forbidden_paths=forbidden_paths,
            forbidden_globs=forbidden_globs,
            forbidden_messages=forbidden_messages,
            forbid_direct_cli_references=forbid_direct_cli_references,
            max_depth=max_depth,
            ignored_prefixes=ignored_prefixes,
            ignored_paths=ignored_paths,
        )

    def ignores(self, rel: str) -> bool:
        normalized = rel if rel.endswith("/") or "." in Path(rel).name else rel
        if normalized in self.ignored_paths:
            return True
        return any(normalized.startswith(prefix) for prefix in (*self.ignored_prefixes, *self.ignored_paths))

    def allows(self, path: Path, rel: str) -> bool:
        if rel in self.allowed_paths or path.name in self.allowed_filenames:
            return True
        return path.suffix.lower() in self.allowed_extensions

    def forbidden_message(self, path: Path, rel: str) -> str | None:
        if rel in self.forbidden_paths:
            return self._message_for(rel, f"forbidden path: {rel}")
        for pattern in self.forbidden_globs:
            if fnmatch.fnmatch(rel, pattern):
                return self._message_for(pattern, f"forbidden path pattern {pattern}: {rel}")
        suffix = path.suffix.lower()
        if suffix in self.forbidden_extensions:
            default = f"forbidden file extension {suffix}: {rel}"
            return self._message_for(suffix, default)
        return None

    def _message_for(self, key: str, default: str) -> str:
        messages = self.forbidden_messages or {}
        return messages.get(key, default)


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


def _is_app_repo(root_name: str) -> bool:
    return root_name not in {"github-pipelines", "python-cli"}


def _allows_shell_scripts(root_name: str) -> bool:
    return root_name == "python-cli"


def _is_allowed_workflow_reference(rel: str) -> bool:
    return rel.startswith(".github/workflows/")


def _has_direct_cli_reference(path: Path) -> bool:
    if path.suffix in {".lock", ".json"} or path.name in {"package-lock.json", "pnpm-lock.yaml"}:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return bool(CLI_REFERENCE_RE.search(text))


def _path_depth(rel: str) -> int:
    return len(Path(rel).parts)


def _check_structure(
    root: Path,
    *,
    slug: str,
    require_layout: bool,
    policy: HygienePolicy | None,
) -> list[str]:
    errors: list[str] = []
    max_depth = policy.max_depth if policy else None
    root_dirs = policy.allowed_root_dirs if policy and policy.allowed_root_dirs else STANDARD_ROOT_DIRS
    root_files = policy.allowed_root_files if policy and policy.allowed_root_files else STANDARD_ROOT_FILES

    enforce_root_allowlist = bool(policy and (policy.allowed_root_dirs or policy.allowed_root_files))
    if require_layout and (slug not in EXEMPT_LAYOUT_REPOS or enforce_root_allowlist):
        for entry in sorted(root.iterdir(), key=lambda path: path.name):
            if entry.name in {".git", ".venv", "node_modules", "__pycache__"}:
                continue
            rel = f"{entry.name}/" if entry.is_dir() else entry.name
            if policy and policy.ignores(rel):
                continue
            if entry.is_dir():
                if entry.name not in root_dirs:
                    errors.append(f"unexpected root directory: {entry.name}/")
            elif entry.is_file() and entry.name not in root_files:
                if enforce_root_allowlist:
                    errors.append(f"unexpected root file: {entry.name}")
                elif policy is None or not policy.allows(entry, entry.name):
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


def policy_with_ignored_paths(policy: HygienePolicy, paths: frozenset[str]) -> HygienePolicy:
    if not paths:
        return policy
    return replace(policy, ignored_paths=frozenset({*policy.ignored_paths, *paths}))


def check_repo_hygiene(
    root: Path,
    *,
    require_layout: bool = False,
    require_structure: bool = False,
    policy: HygienePolicy | None = None,
) -> list[str]:
    root = root.expanduser().resolve()
    slug = repo_slug(root)
    errors: list[str] = []
    forbidden_prefixes = _forbidden_prefixes(slug)

    for path in root.rglob("*"):
        if any(part in {".git", "__pycache__"} for part in path.parts) or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if policy and policy.ignores(rel):
            continue
        if policy:
            forbidden = policy.forbidden_message(path, rel)
            if forbidden:
                errors.append(f"{forbidden}: {rel}" if rel not in forbidden else forbidden)
        if slug != "github-pipelines" and rel.startswith(".github/workflows/"):
            if rel in PIPELINE_WORKFLOW_CONFIGS:
                pass
            elif rel.endswith(".yaml") and rel not in ALLOWED_WORKFLOWS:
                errors.append(f"workflow belongs in github-pipelines: {rel}")
            elif rel.endswith(".yml"):
                errors.append(f"workflow belongs in github-pipelines: {rel}")
        elif any(rel.startswith(prefix) for prefix in forbidden_prefixes):
            if rel.startswith("docker/") and policy and (
                "docker" in policy.allowed_root_dirs
                or rel in policy.allowed_paths
                or any(rel.startswith(f"{allowed}/") for allowed in policy.allowed_paths if allowed.endswith("/"))
            ):
                pass
            else:
                errors.append(f"orchestration/script artifact belongs in python-cli or github-pipelines: {rel}")
        if path.suffix == ".sh" and not _allows_shell_scripts(slug) and not (policy and ".sh" in policy.forbidden_extensions):
            errors.append(
                "shell script belongs in gardusig/python-cli: "
                f"{rel} (move this script to the CLI repo and expose it through a cli command)"
            )
        if (
            policy
            and policy.forbid_direct_cli_references
            and not _is_allowed_workflow_reference(rel)
            and _has_direct_cli_reference(path)
        ):
            errors.append(f"direct cli reference belongs in github-pipelines: {rel}")
        if policy and not policy.allows(path, rel):
            errors.append(f"file type is not allowed by hygiene policy: {rel}")

    if require_layout and slug not in EXEMPT_LAYOUT_REPOS:
        if not (root / "README.md").is_file():
            errors.append("missing required file: README.md")
        for dirname in ("src", "docs"):
            if not (root / dirname).is_dir():
                if dirname == "docs" and policy and "docs" in policy.allowed_root_dirs:
                    continue
                errors.append(f"missing required directory: {dirname}/")
        if not (root / "test").is_dir() and not (root / "tests").is_dir():
            errors.append("missing required test directory: test/ or tests/")

    if require_structure or (policy and policy.max_depth is not None):
        errors.extend(_check_structure(root, slug=slug, require_layout=require_layout or require_structure, policy=policy))
    return errors
