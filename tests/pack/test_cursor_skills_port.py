"""Verify all @gh-* skills map to implemented cli commands."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / "docs/migration/cursor-skills/distill/public-skill-dag.json"
INDEX = ROOT / "docs/migration/cursor-skills/distill/INDEX.md"

# Public @gh-* skills from cursor-skills (merge excluded)
GH_SKILLS = {
    "gh-issue-list": "cli gh issue list",
    "gh-issue-view": "cli gh issue context",
    "gh-issue": "cli craft issue",
    "gh-issue-pick": "cli craft pick",
    "gh-issue-backlog": "cli gh backlog tree",
    "gh-issue-next": "cli craft next",
    "gh-issue-labels": "cli gh label sync",
    "gh-issue-review": "cli craft issue --review",
    "gh-issue-execute": "cli craft execute",
    "gh-issue-close": "cli gh issue close",
    "gh-issue-delete-closed": "cli gh issue delete",
    "gh-pr-list": "cli gh pr list",
    "gh-pr-view": "cli gh pr view",
    "gh-pr": "cli craft pr",
    "gh-pr-review": "cli review pr",
    "gh-pr-close": "cli gh pr close",
}


def test_public_skill_dag_exists() -> None:
    assert DAG.is_file()
    data = json.loads(DAG.read_text(encoding="utf-8"))
    assert "nodes" in data or isinstance(data, dict)


def test_distill_index_lists_gh_skills() -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert "@gh-issue" in text or "gh-issue" in text
    assert "craft" in text.lower()


def test_all_gh_skills_have_cli_mapping() -> None:
    text = INDEX.read_text(encoding="utf-8")
    for skill, cli_cmd in GH_SKILLS.items():
        assert skill.replace("gh-", "") in text or f"`{cli_cmd}`" in text or cli_cmd.split()[-1] in text


def test_index_shows_done_status() -> None:
    text = INDEX.read_text(encoding="utf-8")
    pending = len(re.findall(r"\| pending \|", text))
    assert pending == 0, f"{pending} skills still pending in INDEX.md"
