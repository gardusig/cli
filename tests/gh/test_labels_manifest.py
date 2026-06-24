"""Label manifest guardrails for backlog taxonomy (issue #53)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import yaml


MANIFEST = ROOT / "config" / "gh" / "labels.manifest.yaml"


def test_labels_manifest_exists_and_parses() -> None:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    names = [entry["name"] for entry in data["labels"]]
    assert "issue-type:epic" in names
    assert "issue-type:child" in names
    assert "epic:01-gh" in names
    assert "epic:03-notion" in names
    assert "bug" in data["protected"]


def test_labels_manifest_epic_slugs_match_backlog() -> None:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    epics = {n for n in (entry["name"] for entry in data["labels"]) if n.startswith("epic:")}
    expected = {
        "epic:00-infra",
        "epic:01-gh",
        "epic:02-chrome",
        "epic:03-notion",
        "epic:04-drive",
        "epic:05-contest",
        "epic:06-pypi",
        "epic:07-cli-review",
        "epic:08-projects",
        "epic:09-git",
        "epic:10-gh-pr",
        "epic:11-gh-hub",
        "epic:12-docker",
    }
    assert expected <= epics
