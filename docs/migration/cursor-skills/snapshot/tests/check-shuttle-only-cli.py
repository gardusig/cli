#!/usr/bin/env python3
"""Fail when skill bash fences use raw gh/git instead of shuttle."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"

BASH_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
RAW_GH = re.compile(r"^\s*gh\s+", re.MULTILINE)
RAW_GIT = re.compile(r"^\s*git(?:\s+-C\s+[^\s]+)?\s+", re.MULTILINE)

# Doc scaffolds for other repos may mention git in prose only — no bash fences there.
EXEMPT_PREFIXES = (
    "skills/internal/read/docs/",
)


def main() -> int:
    errors: list[str] = []
    for path in sorted(SKILLS_ROOT.rglob("SKILL.md")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if any(rel.startswith(p) for p in EXEMPT_PREFIXES):
            continue
        text = path.read_text(encoding="utf-8")
        for match in BASH_FENCE.finditer(text):
            block = match.group(1)
            if RAW_GH.search(block) or RAW_GIT.search(block):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: bash fence contains raw gh/git (use shuttle gh|git)")
                break

    if errors:
        for e in sorted(errors):
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("OK: skill bash fences use shuttle-only terminal commands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
