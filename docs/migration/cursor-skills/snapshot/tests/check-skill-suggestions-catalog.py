#!/usr/bin/env python3
"""Every public @gh-* skill must have a next-steps catalog section."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
ROOT = _TESTS_DIR.parents[1]
CATALOG = ROOT / "skills/internal/read/skill-suggestions/next-steps-options/SKILL.md"
PUBLIC_ROOTS = (ROOT / "skills/gh",)

_SECTION = re.compile(r"^### `([^`]+)`\s*$", re.MULTILINE)
_FRONTMATTER_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)


def _public_skill_names() -> set[str]:
    names: set[str] = set()
    for base in PUBLIC_ROOTS:
        for path in base.rglob("SKILL.md"):
            text = path.read_text(encoding="utf-8")
            m = _FRONTMATTER_NAME.search(text)
            if m:
                names.add(m.group(1))
    return names


def _catalog_sections() -> set[str]:
    text = CATALOG.read_text(encoding="utf-8")
    return set(_SECTION.findall(text))


def main() -> int:
    public = _public_skill_names()
    catalog = _catalog_sections()
    missing = sorted(public - catalog)
    extra = sorted(catalog - public)

    errors = 0
    if missing:
        print("FAIL: public skills missing next-steps catalog section:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        errors += len(missing)
    if extra:
        print("FAIL: catalog sections with no public skill:", file=sys.stderr)
        for name in extra:
            print(f"  - {name}", file=sys.stderr)
        errors += len(extra)

    if errors:
        return 1
    print(f"OK: {len(public)} public skills covered in next-steps catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
