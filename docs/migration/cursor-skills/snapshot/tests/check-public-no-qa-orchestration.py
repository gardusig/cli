#!/usr/bin/env python3
"""Public skills must not orchestrate AskQuestion — delegate to write gate / read-skill-suggestions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"

_LANG_SECTION = re.compile(
    r"^##\s+Language interaction policy\b.*?(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
_REC_SECTION = re.compile(
    r"^##\s+Recommended next steps\b.*?(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
# Allowed: "no AskQuestion by default" in YAML description or read-only inventory skills.
_ORCHESTRATION_PATTERNS = (
    re.compile(r"\*\*AskQuestion\*\*", re.IGNORECASE),
    re.compile(r"Run .{0,40}AskQuestion", re.IGNORECASE),
    re.compile(r"Goal \+ AskQuestion", re.IGNORECASE),
    re.compile(r"AskQuestion intent gate", re.IGNORECASE),
    re.compile(r"AskQuestion before", re.IGNORECASE),
    re.compile(r"refinement AskQuestion", re.IGNORECASE),
)


def _body_without_exempt_sections(text: str) -> str:
    body = text
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        if end != -1:
            body = body[end + 5 :]
    body = _LANG_SECTION.sub("", body)
    body = _REC_SECTION.sub("", body)
    return body


def main() -> int:
    errors = 0
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = REPO_ROOT / line
        raw = path.read_text(encoding="utf-8")
        scan = _body_without_exempt_sections(raw)
        for pat in _ORCHESTRATION_PATTERNS:
            if pat.search(scan):
                rel = path.relative_to(REPO_ROOT)
                print(
                    f"FAIL: {rel}: inline AskQuestion orchestration — use write gate "
                    f"(read-safety-structured-qa §0) or read-skill-suggestions",
                    file=sys.stderr,
                )
                errors += 1
                break
    if errors:
        return 1
    print("Public skill Q&A boundary checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
