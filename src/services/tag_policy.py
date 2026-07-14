"""Git tag naming policies — per-repo patterns, detection, and next-tag suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path

import yaml

from src.services.pypi_publish import PyPiPublishError, read_project_version

TAG_POLICY_REL = Path("config") / "tag.yaml"

_SEMVER_CORE = r"\d+\.\d+\.\d+([-.][0-9A-Za-z.]+)?"


class TagPattern(str, Enum):
    """Supported tag naming conventions."""

    SEMVER_V = "semver-v"  # v1.2.3 (PyPI / GitHub releases)
    SEMVER = "semver"  # 1.2.3
    DATE = "date"  # YYYY-MM-DD
    PLAIN = "plain"  # any non-empty tag (no ordering)


_PATTERN_RES: dict[TagPattern, re.Pattern[str]] = {
    TagPattern.SEMVER_V: re.compile(rf"^v{_SEMVER_CORE}$"),
    TagPattern.SEMVER: re.compile(rf"^{_SEMVER_CORE}$"),
    TagPattern.DATE: re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    TagPattern.PLAIN: re.compile(r"^[^\s/]+$"),
}

_PATTERN_EXAMPLES: dict[TagPattern, str] = {
    TagPattern.SEMVER_V: "v0.1.0",
    TagPattern.SEMVER: "1.0.0",
    TagPattern.DATE: "2026-06-24",
    TagPattern.PLAIN: "release-candidate",
}

_BUMP_LEVELS = frozenset({"patch", "minor", "major"})


@dataclass(frozen=True)
class TagPolicy:
    pattern: TagPattern
    bump: str = "patch"
    require_increase: bool = False

    @classmethod
    def from_mapping(cls, data: object) -> TagPolicy:
        if not isinstance(data, dict):
            raise PyPiPublishError(f"invalid {TAG_POLICY_REL}: expected mapping")
        raw_pattern = str(data.get("pattern", TagPattern.PLAIN.value)).strip().lower()
        try:
            pattern = TagPattern(raw_pattern)
        except ValueError as exc:
            allowed = ", ".join(p.value for p in TagPattern)
            raise PyPiPublishError(
                f"invalid tag pattern {raw_pattern!r} in {TAG_POLICY_REL}; use: {allowed}"
            ) from exc
        bump = str(data.get("bump", "patch")).strip().lower()
        if bump not in _BUMP_LEVELS:
            raise PyPiPublishError(
                f"invalid bump {bump!r} in {TAG_POLICY_REL}; use: patch, minor, major"
            )
        require_increase = bool(data.get("require_increase", False))
        if "require_increase" not in data and pattern in (
            TagPattern.SEMVER_V,
            TagPattern.SEMVER,
        ):
            require_increase = True
        return cls(pattern=pattern, bump=bump, require_increase=require_increase)


def load_tag_policy_file(repo_root: Path) -> TagPolicy | None:
    path = repo_root / TAG_POLICY_REL
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PyPiPublishError(f"invalid YAML in {TAG_POLICY_REL}: {exc}") from exc
    return TagPolicy.from_mapping(data or {})


def classify_tag(name: str) -> set[TagPattern]:
    matched: set[TagPattern] = set()
    for pattern, regex in _PATTERN_RES.items():
        if regex.fullmatch(name.strip()):
            matched.add(pattern)
    return matched


def detect_tag_pattern(tags: list[str]) -> TagPattern | None:
    """Pick the dominant pattern from existing tag names."""
    if not tags:
        return None
    counts: dict[TagPattern, int] = {p: 0 for p in TagPattern}
    for name in tags:
        kinds = classify_tag(name)
        if TagPattern.SEMVER_V in kinds:
            counts[TagPattern.SEMVER_V] += 1
        elif TagPattern.SEMVER in kinds:
            counts[TagPattern.SEMVER] += 1
        elif TagPattern.DATE in kinds:
            counts[TagPattern.DATE] += 1
        else:
            counts[TagPattern.PLAIN] += 1
    best = max(counts.items(), key=lambda item: item[1])
    if best[1] == 0:
        return None
    return best[0]


def infer_tag_pattern(repo_root: Path, tags: list[str]) -> TagPattern:
    """Resolve policy when ``config/tag.yaml`` is absent."""
    detected = detect_tag_pattern(tags)
    if detected is not None:
        return detected
    if (repo_root / "pyproject.toml").is_file():
        return TagPattern.SEMVER
    return TagPattern.PLAIN


def resolve_tag_policy(repo_root: Path, tags: list[str]) -> TagPolicy:
    explicit = load_tag_policy_file(repo_root)
    if explicit is not None:
        return explicit
    pattern = infer_tag_pattern(repo_root, tags)
    require_increase = pattern in (TagPattern.SEMVER_V, TagPattern.SEMVER)
    return TagPolicy(pattern=pattern, bump="patch", require_increase=require_increase)


def latest_tag(tags: list[str], policy: TagPolicy) -> str | None:
    """Highest existing tag name for *policy* (among *tags*)."""
    return _max_tag(tags, policy.pattern)


def matches_pattern(name: str, pattern: TagPattern) -> bool:
    return pattern in classify_tag(name)


def parse_semver_tuple(version: str) -> tuple[int, int, int]:
    core = version.strip()
    if core.startswith("v"):
        core = core[1:]
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", core)
    if not match:
        raise PyPiPublishError(f"not a semver tag: {version!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def compare_semver_tags(a: str, b: str) -> int:
    """Return -1, 0, or 1 (``a`` vs ``b``)."""
    ta = parse_semver_tuple(a)
    tb = parse_semver_tuple(b)
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def compare_versions(a: str, b: str) -> int:
    """Compare bare semver strings (no ``v`` prefix required)."""
    return compare_semver_tags(f"v{a}", f"v{b}")


def bump_semver(version: str, *, level: str = "patch") -> str:
    major, minor, patch = parse_semver_tuple(version)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _max_tag(tags: list[str], pattern: TagPattern) -> str | None:
    matching = [t for t in tags if matches_pattern(t, pattern)]
    if not matching:
        return None
    if pattern in (TagPattern.SEMVER_V, TagPattern.SEMVER):
        return max(matching, key=lambda t: parse_semver_tuple(t))
    if pattern == TagPattern.DATE:
        return max(matching)
    return max(matching)


def suggest_next_tag(
    tags: list[str],
    policy: TagPolicy,
    *,
    repo_root: Path | None = None,
) -> str:
    """Next tag name following *policy* and existing *tags*."""
    latest = _max_tag(tags, policy.pattern)
    if latest is not None:
        if policy.pattern in (TagPattern.SEMVER_V, TagPattern.SEMVER):
            core = latest[1:] if latest.startswith("v") else latest
            bumped = bump_semver(core, level=policy.bump)
            if policy.pattern == TagPattern.SEMVER_V:
                return f"v{bumped}"
            return bumped
        if policy.pattern == TagPattern.DATE:
            return date.today().isoformat()
        raise PyPiPublishError(
            f"cannot suggest next tag for pattern {policy.pattern.value!r}; "
            f"latest is {latest!r} — pass an explicit tag name"
        )

    if policy.pattern == TagPattern.SEMVER_V:
        root = (repo_root or Path.cwd()).resolve()
        if (root / "pyproject.toml").is_file():
            try:
                return f"v{read_project_version(root)}"
            except PyPiPublishError:
                pass
        return _PATTERN_EXAMPLES[TagPattern.SEMVER_V]
    if policy.pattern == TagPattern.SEMVER:
        root = (repo_root or Path.cwd()).resolve()
        if (root / "pyproject.toml").is_file():
            try:
                return read_project_version(root)
            except PyPiPublishError:
                pass
        return _PATTERN_EXAMPLES[TagPattern.SEMVER]
    if policy.pattern == TagPattern.DATE:
        return date.today().isoformat()
    raise PyPiPublishError(
        "no existing tags and pattern is plain — pass an explicit tag name"
    )


def validate_tag_name(
    name: str,
    policy: TagPolicy,
    *,
    tags: list[str] | None = None,
) -> str:
    """Validate *name* against *policy*; return normalized tag."""
    tag = name.strip()
    if not tag:
        raise PyPiPublishError("tag name cannot be empty")
    if not matches_pattern(tag, policy.pattern):
        example = _PATTERN_EXAMPLES[policy.pattern]
        raise PyPiPublishError(
            f"tag {name!r} does not match pattern {policy.pattern.value} "
            f"(example: {example})"
        )
    if policy.require_increase and tags and policy.pattern in (
        TagPattern.SEMVER_V,
        TagPattern.SEMVER,
    ):
        latest = _max_tag(tags, policy.pattern)
        if latest is not None and compare_semver_tags(tag, latest) <= 0:
            suggested = suggest_next_tag(tags, policy)
            raise PyPiPublishError(
                f"tag {tag!r} must be greater than latest {latest!r}; "
                f"suggested: {suggested}"
            )
    return tag


def policy_summary(policy: TagPolicy, *, suggested: str | None = None) -> list[str]:
    lines = [f"tag_pattern: {policy.pattern.value}", f"tag_bump: {policy.bump}"]
    if policy.require_increase:
        lines.append("tag_require_increase: yes")
    if suggested:
        lines.append(f"tag_suggested: {suggested}")
    return lines
