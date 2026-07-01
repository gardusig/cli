#!/usr/bin/env python3
"""Every public skill must document skip ENV flags and suggestions contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"

REQUIRED_PHRASES = (
    "## Skip & suggestions",
    "skip=false",
    "skip=true",
    "SKIP_SUGGESTIONS",
    "SKIP_QA_WRITE",
)


def main() -> int:
    errors = 0
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = REPO_ROOT / line
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT)
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                print(f"FAIL: {rel} missing {phrase!r}", file=sys.stderr)
                errors += 1
        if not re.search(r"SKIP_QA_[A-Z0-9_]+=true", text):
            print(f"FAIL: {rel} missing per-skill SKIP_QA_* flag", file=sys.stderr)
            errors += 1
        rec = re.search(r"^## Recommended next steps\b", text, re.MULTILINE)
        if not rec or "read-skill-suggestions" not in text[rec.start() :]:
            print(f"FAIL: {rel} Recommended next steps must reference read-skill-suggestions", file=sys.stderr)
            errors += 1
    if errors:
        return 1
    print("Public skill skip/suggestions checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
