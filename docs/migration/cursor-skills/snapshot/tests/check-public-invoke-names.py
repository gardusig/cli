#!/usr/bin/env python3
"""Fail when a public skill body uses @handles that do not match installed name: values."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"
_AT = re.compile(r"@([a-z][a-z0-9-]*)\b", re.IGNORECASE)
_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)


def main() -> int:
    public_names: set[str] = set()
    paths: list[Path] = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            paths.append(REPO_ROOT / line)

    for path in paths:
        text = path.read_text(encoding="utf-8")
        m = _NAME.search(text)
        if not m:
            print(f"FAIL: missing name in {path.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        public_names.add(m.group(1).lower())

    errors = 0
    legacy = {f"gh-issue-{n[len('gh-issue-'):]}" for n in public_names if n.startswith("gh-issue-") and n != "gh-issue"}

    for path in paths:
        text = path.read_text(encoding="utf-8")
        own = _NAME.search(text)
        if not own:
            continue
        own_name = own.group(1).lower()
        for m in _AT.finditer(text):
            handle = m.group(1).lower()
            if handle == own_name:
                continue
            if handle in public_names:
                continue
            if handle in legacy:
                print(
                    f"FAIL: {path.relative_to(REPO_ROOT)} uses @{handle} "
                    f"(legacy; use gh-issue-* install names)",
                    file=sys.stderr,
                )
                errors += 1

    if errors:
        return 1
    print("Public @ invoke names OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
