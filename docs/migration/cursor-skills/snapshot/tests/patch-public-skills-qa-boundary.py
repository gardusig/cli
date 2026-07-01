#!/usr/bin/env python3
"""One-shot maintainer script: align public skills with write-gate / no inline Q&A policy."""

from __future__ import annotations

import re
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"

OLD_REC = re.compile(
    r"## Recommended next steps\n\n"
    r"After \*\*Verification\*\*, use \*\*\[`read-skill-suggestions`\]\([^)]+\)\*\* with the current public skill "
    r"\*\*`name:`\*\* and \*\*\[`read-safety-structured-qa`\]\([^)]+\) §9\*\*\. Offer \*\*one\*\* optional "
    r"\*\*AskQuestion\*\* with the top \*\*1-3\*\* ranked options whose \*\*When\*\* applies\. Set \*\*`skip=false`\*\* "
    r"only for the root user-invoked public skill and pass \*\*`skip=true`\*\* for every nested child public-skill call\. "
    r"Skip prompting when the user already named the next skill, declined further work, or a permitted \*\*`SKIP_QA_\*`\*\* "
    r"bypass applies\.",
    re.MULTILINE,
)

NEW_REC_TEMPLATE = (
    "## Recommended next steps\n\n"
    "After **Verification**, delegate to **[`read-skill-suggestions`]({sug})** "
    "(`skip=false` only for the root user-invoked public skill; `skip=true` for nested child public-skill calls)."
)


def rel_to_suggestions(skill_path: Path) -> str:
    depth = len(skill_path.relative_to(REPO_ROOT / "skills").parts) - 1
    return "../" * depth + "internal/read/skill-suggestions/SKILL.md"


def patch_recommended(body: str, skill_path: Path) -> str:
    sug = rel_to_suggestions(skill_path)
    new = NEW_REC_TEMPLATE.format(sug=sug)
    if OLD_REC.search(body):
        return OLD_REC.sub(new, body, count=1)
    if "## Recommended next steps" in body and "delegate to" in body:
        return body
    return body


def main() -> None:
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = REPO_ROOT / line
        text = path.read_text(encoding="utf-8")
        updated = patch_recommended(text, path)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            print(f"updated recommended next steps: {line}")


if __name__ == "__main__":
    main()
