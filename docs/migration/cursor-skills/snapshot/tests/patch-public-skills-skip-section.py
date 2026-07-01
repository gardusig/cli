#!/usr/bin/env python3
"""Align public skills: ## Skip & suggestions + Recommended next steps contract."""

from __future__ import annotations

import re
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"

# skill name (YAML) -> SKIP_QA env token in existing files
SKIP_QA_BY_NAME: dict[str, str] = {
    "gh-issue-execute": "SKIP_QA_GH_ISSUES_EXECUTE",
    "gh-issue": "SKIP_QA_GH_ISSUES",
    "gh-issue-close": "SKIP_QA_GH_ISSUES_CLOSE",
    "gh-issue-labels": "SKIP_QA_GH_ISSUES_LABELS",
    "gh-issue-backlog": "SKIP_QA_GH_ISSUES_BACKLOG",
    "gh-issue-next": "SKIP_QA_GH_ISSUES_NEXT",
    "gh-issue-delete-closed": "SKIP_QA_GH_ISSUES_DELETE_CLOSED",
    "gh-issue-list": "SKIP_QA_GH_ISSUES_LIST",
    "gh-issue-pick": "SKIP_QA_GH_ISSUES_PICK",
    "gh-issue-review": "SKIP_QA_GH_ISSUES_REVIEW",
    "gh-issue-view": "SKIP_QA_GH_ISSUES_VIEW",
    "gh-pr": "SKIP_QA_GH_PR",
    "gh-pr-close": "SKIP_QA_GH_PR_CLOSE",
    "gh-pr-list": "SKIP_QA_GH_PR_LIST",
    "gh-pr-view": "SKIP_QA_GH_PR_VIEW",
    "gh-pr-review": "SKIP_QA_GH_PR_REVIEW",
}

SKIP_SECTION = """## Skip & suggestions

| Flag / param | Role |
| --- | --- |
| **`skip=false`** | Root invocation — offer next-step suggestions after **Verification** |
| **`skip=true`** | Nested public-skill child call — no next-step prompt |
| **`{skip_qa}=true`** | Bypass routine write gates for this skill |
| **`SKIP_QA_WRITE=true`** | Shared write-flow Q&A bypass where allowed |
| **`SKIP_SUGGESTIONS=true`** | Suppress next-step suggestions even at root |

High-risk or destructive confirmations still require explicit user confirmation when bypass flags are set.
"""

REC_TEMPLATE = """## Recommended next steps

When **`skip=false`** (root invocation) and **`SKIP_SUGGESTIONS`** is unset, delegate to **[`read-skill-suggestions`]({sug})** for optional next-step choices (**summary** → **options** → AskQuestion). Nested public-skill calls use **`skip=true`**.
"""

OLD_QA_HEADING = re.compile(r"^## Q&A bypass ENV\b", re.MULTILINE)
OLD_REC = re.compile(
    r"^## Recommended next steps\n\nAfter \*\*Verification\*\*, delegate to \*\*\[`read-skill-suggestions`\]\([^)]+\)\*\* "
    r"\(`skip=false` only for the root user-invoked public skill; `skip=true` for nested child public-skill calls\)\.",
    re.MULTILINE,
)


def _parse_name(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def rel_to_suggestions(skill_path: Path) -> str:
    depth = len(skill_path.relative_to(REPO_ROOT / "skills").parts) - 1
    return "../" * depth + "internal/read/skill-suggestions/SKILL.md"


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    name = _parse_name(text)
    if not name or name not in SKIP_QA_BY_NAME:
        return False
    skip_qa = SKIP_QA_BY_NAME[name]
    updated = text

    if OLD_QA_HEADING.search(updated):
        start = OLD_QA_HEADING.search(updated).start()
        end = updated.find("\n## ", start + 1)
        if end == -1:
            end = len(updated)
        updated = updated[:start] + SKIP_SECTION.format(skip_qa=skip_qa) + updated[end:]

    sug = rel_to_suggestions(path)
    new_rec = REC_TEMPLATE.format(sug=sug)
    if OLD_REC.search(updated):
        updated = OLD_REC.sub(new_rec, updated, count=1)

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = REPO_ROOT / line
        if patch_file(path):
            print(f"patched: {line}")
            changed += 1
    print(f"done ({changed} files)")


if __name__ == "__main__":
    main()
