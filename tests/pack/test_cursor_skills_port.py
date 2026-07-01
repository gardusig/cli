"""Pack tests ported from cursor-skills snapshot — routing and DAG checks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / "docs/migration/cursor-skills/distill/public-skill-dag.json"
INDEX = ROOT / "docs/migration/cursor-skills/distill/INDEX.md"


def test_public_skill_dag_exists() -> None:
    assert DAG.is_file()
    data = json.loads(DAG.read_text(encoding="utf-8"))
    assert "nodes" in data or isinstance(data, dict)


def test_distill_index_lists_gh_skills() -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert "@gh-issue" in text or "gh-issue" in text
    assert "craft" in text.lower()
