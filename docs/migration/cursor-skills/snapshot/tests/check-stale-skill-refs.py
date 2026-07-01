#!/usr/bin/env python3
"""Fail on references to removed skills, libraries, or legacy prefixes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
SCAN_ROOTS = [
    REPO_ROOT / "skills",
    REPO_ROOT / "docs",
]

PATTERNS = [
    (re.compile(r"internal-read-|internal-write-", re.I), "legacy internal- prefix"),
    (re.compile(r"skills/gh/projects/", re.I), "removed skills/gh/projects/"),
    (re.compile(r"@gh-project-", re.I), "@gh-project-* public skill"),
    (re.compile(r"@git-zip\b", re.I), "@git-zip invoke"),
    (re.compile(r"gh-pr-skills", re.I), "gh-pr-skills"),
    (re.compile(r"docs/internal\.md", re.I), "docs/internal.md"),
    (re.compile(r"issue-projects-relationships", re.I), "issue-projects-relationships"),
    (re.compile(r"project-item-list", re.I), "project-item-list"),
    (re.compile(r"write-project-commands", re.I), "write-project-commands"),
    (re.compile(r"skills/read/plan/", re.I), "removed skills/read/plan/"),
    (re.compile(r"skills/write/plan/", re.I), "removed skills/write/plan/"),
    (re.compile(r"\bread-plan-", re.I), "removed read-plan-* library prefix"),
    (re.compile(r"\bwrite-plan-", re.I), "removed write-plan-* library prefix"),
    (re.compile(r"skills/read/gh/issue-description/work-plan", re.I), "removed work-plan library"),
    (re.compile(r"\bcursor-plan-ui\b", re.I), "removed cursor-plan-ui DAG node"),
    (re.compile(r"\bcursorPlanUI\b"), "removed cursorPlanUI mermaid id"),
    (re.compile(r"Cursor Plan", re.I), "removed Cursor Plan product references"),
    (re.compile(r"\.cursor/plan\.md", re.I), "removed .cursor/plan.md convention"),
    (re.compile(r"@plan-", re.I), "removed @plan-* public skills"),
    (re.compile(r"plan-refine|plan-execute", re.I), "removed plan-refine/plan-execute skills"),
]


def main() -> int:
    errors: list[str] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files = [root]
        else:
            files = list(root.rglob("*"))
        for path in files:
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".sh", ".py", ".json", ".txt", ".yml"}:
                continue
            if path.name.startswith("check-") and path.parent.name == "tests":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for rx, label in PATTERNS:
                if "project-structure-eval" in str(path) and "project-item-list" in label:
                    continue
                if "projectCards" in text and "project-item-list" in label:
                    continue
                for m in rx.finditer(text):
                    if label == "project-item-list" and "project-structure-eval" in text[max(0, m.start() - 30) : m.end() + 30]:
                        continue
                    line = text.count("\n", 0, m.start()) + 1
                    errors.append(f"{path.relative_to(REPO_ROOT)}:{line}: {label}")
                    break

    if errors:
        for e in sorted(set(errors))[:50]:
            print(f"FAIL: {e}", file=sys.stderr)
        if len(errors) > 50:
            print(f"... and {len(errors) - 50} more", file=sys.stderr)
        return 1
    print("No stale skill references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
