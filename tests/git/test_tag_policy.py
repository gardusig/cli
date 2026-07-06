"""Tag policy detection, validation, and suggestions."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.pypi_publish import PyPiPublishError
from src.services.tag_policy import (
    TagPattern,
    TagPolicy,
    bump_semver,
    classify_tag,
    compare_semver_tags,
    detect_tag_pattern,
    latest_tag,
    resolve_tag_policy,
    suggest_next_tag,
    validate_tag_name,
)


def test_classify_tag_semver_v() -> None:
    assert TagPattern.SEMVER_V in classify_tag("v1.2.3")
    assert TagPattern.SEMVER_V not in classify_tag("1.2.3")
    assert TagPattern.DATE in classify_tag("2026-06-24")


def test_detect_tag_pattern_majority() -> None:
    tags = ["v0.1.0", "v0.1.1", "2026-01-01"]
    assert detect_tag_pattern(tags) == TagPattern.SEMVER_V


def test_suggest_next_semver_v_bumps_patch() -> None:
    policy = TagPolicy(pattern=TagPattern.SEMVER_V, bump="patch")
    assert suggest_next_tag(["v0.1.0"], policy) == "v0.1.1"
    assert suggest_next_tag(["v0.1.0", "v0.1.2"], policy) == "v0.1.3"


def test_suggest_next_date_is_today() -> None:
    policy = TagPolicy(pattern=TagPattern.DATE)
    suggested = suggest_next_tag(["2026-01-01"], policy)
    assert len(suggested) == 10
    assert suggested[4] == "-"


def test_validate_require_increase() -> None:
    policy = TagPolicy(pattern=TagPattern.SEMVER_V, require_increase=True)
    with pytest.raises(PyPiPublishError, match="greater than latest"):
        validate_tag_name("v0.1.0", policy, tags=["v0.1.0"])
    assert validate_tag_name("v0.1.1", policy, tags=["v0.1.0"]) == "v0.1.1"


def test_load_tag_policy_from_repo(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "tag.yaml").write_text(
        "pattern: date\nbump: patch\n",
        encoding="utf-8",
    )
    policy = resolve_tag_policy(tmp_path, [])
    assert policy.pattern == TagPattern.DATE


def test_infer_semver_v_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.2.0"\n',
        encoding="utf-8",
    )
    policy = resolve_tag_policy(tmp_path, [])
    assert policy.pattern == TagPattern.SEMVER_V
    assert policy.require_increase is True
    assert suggest_next_tag([], policy, repo_root=tmp_path) == "v0.2.0"


def test_latest_tag_picks_highest_semver() -> None:
    policy = TagPolicy(pattern=TagPattern.SEMVER_V)
    tags = ["v0.1.0", "v0.1.2", "v0.1.1"]
    assert latest_tag(tags, policy) == "v0.1.2"


def test_compare_semver_tags() -> None:
    assert compare_semver_tags("v0.1.0", "v0.1.1") < 0
    assert compare_semver_tags("v1.0.0", "v0.9.9") > 0


def test_bump_semver_levels() -> None:
    assert bump_semver("0.1.0", level="patch") == "0.1.1"
    assert bump_semver("0.1.0", level="minor") == "0.2.0"
    assert bump_semver("0.1.0", level="major") == "1.0.0"
