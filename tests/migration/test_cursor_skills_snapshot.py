"""Integrity checks for embedded cursor-skills migration snapshot."""

from __future__ import annotations

import json
from pathlib import Path

MIGRATION_ROOT = Path(__file__).resolve().parents[2] / "docs" / "migration" / "cursor-skills"
SNAPSHOT = MIGRATION_ROOT / "snapshot"
MANIFEST = MIGRATION_ROOT / "MANIFEST.json"


def test_manifest_exists_and_lists_files() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["source_repo"] == "gardusig/cursor-skills"
    assert len(data["source_commit"]) == 40
    assert len(data["files"]) >= 140


def test_key_skill_paths_present() -> None:
    required = [
        "skills/gh/issue/execute/SKILL.md",
        "skills/gh/pr/SKILL.md",
        "skills/gh/pr/review/SKILL.md",
        "skills/internal/read/shuttle/gh/SKILL.md",
        "skills/internal/read/workflow/workflows/SKILL.md",
        "tests/public-skills.txt",
        "tests/fixtures/public-skill-dag/graph.json",
        "docs/gh.md",
    ]
    for rel in required:
        assert (SNAPSHOT / rel).is_file(), f"missing snapshot file: {rel}"


def test_distill_index_and_dag() -> None:
    assert (MIGRATION_ROOT / "distill" / "INDEX.md").is_file()
    assert (MIGRATION_ROOT / "distill" / "public-skill-dag.json").is_file()
    dag = json.loads((MIGRATION_ROOT / "distill" / "public-skill-dag.json").read_text())
    assert dag["version"] == 1
    assert len(dag["nodes"]) >= 16
