"""Integration fixtures and CI config must not reference developer home paths."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.constants import ROOT

FORBIDDEN_PATH_FRAGMENTS = (
    "~/git-local",
    "/Users/",
    "Mobile Documents",
    "iCloud",
)


@pytest.mark.parametrize(
    "rel_path",
    [
        "config/ci/config.yaml",
        "tests/fixtures/workflows/plan-to-issues/config.yaml",
    ],
)
def test_integration_config_avoids_host_paths(rel_path: str) -> None:
    path = ROOT / rel_path
    assert path.is_file(), f"missing {rel_path}"
    text = path.read_text(encoding="utf-8")
    for fragment in FORBIDDEN_PATH_FRAGMENTS:
        assert fragment not in text, f"{rel_path} must not contain {fragment!r}"


def test_ci_config_uses_repo_relative_paths() -> None:
    data = yaml.safe_load((ROOT / "config/ci/config.yaml").read_text(encoding="utf-8"))
    tags_dir = Path(str(data["backup"]["tags_dir"]))
    assert not tags_dir.is_absolute() or str(tags_dir).startswith("/tmp")
    for repo in data["backup"]["repositories"]:
        repo_path = Path(str(repo["path"]))
        assert repo_path == Path(".")


def test_gh_workspace_fixtures_use_relative_urls() -> None:
    issues = ROOT / "tests/fixtures/gh/workspace/issues.json"
    text = issues.read_text(encoding="utf-8")
    assert "github.com/example" in text
    assert "/Users/" not in text
