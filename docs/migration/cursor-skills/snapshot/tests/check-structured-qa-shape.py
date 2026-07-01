#!/usr/bin/env python3
"""Regression checks for structured Q&A shape and English-first policy."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"

# Anti-patterns that push detail into AskQuestion prompts instead of chat summaries.
BANNED_PHRASES = (
    "summary in the prompt text",
    "summary in prompt",
    "in the prompt text",
    "embed PR titles, bodies",
)

STRUCTURED_QA = SKILLS_ROOT / "internal/read/safety/structured-qa/SKILL.md"
LANGUAGE_RULES = SKILLS_ROOT / "internal/read/safety/language-interaction-rules/SKILL.md"

REQUIRED_IN_STRUCTURED_QA = (
    "§0",
    "§1f",
    "read-safety-structured-qa-summary",
    "read-safety-structured-qa-question",
    "read-safety-structured-qa-options",
    "assistant message immediately above",
    "Do not paste full PR/issue bodies",
)

REQUIRED_IN_LANGUAGE_RULES = (
    "Never",
    "localize Q&A",
    "Always English",
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def scan_skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.rglob("SKILL.md"))


def check_banned_phrases() -> None:
    for path in scan_skill_files():
        if path == STRUCTURED_QA:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in BANNED_PHRASES:
            if phrase in text:
                rel = path.relative_to(REPO_ROOT)
                fail(f"{rel} contains banned Q&A phrase: {phrase!r}")


def check_canonical_files() -> None:
    if not STRUCTURED_QA.is_file():
        fail(f"missing {STRUCTURED_QA.relative_to(REPO_ROOT)}")
    if not LANGUAGE_RULES.is_file():
        fail(f"missing {LANGUAGE_RULES.relative_to(REPO_ROOT)}")

    sq_text = STRUCTURED_QA.read_text(encoding="utf-8")
    for needle in REQUIRED_IN_STRUCTURED_QA:
        if needle not in sq_text:
            fail(f"structured-qa missing required phrase: {needle!r}")

    lang_text = LANGUAGE_RULES.read_text(encoding="utf-8")
    for needle in REQUIRED_IN_LANGUAGE_RULES:
        if needle not in lang_text:
            fail(f"language-interaction-rules missing required phrase: {needle!r}")


def check_preflight_qa_references() -> None:
    preflight_paths = [
        SKILLS_ROOT / "internal/read/pr/preflight-qa/SKILL.md",
        SKILLS_ROOT / "internal/read/issue/preflight-qa/SKILL.md",
    ]
    for path in preflight_paths:
        if not path.is_file():
            fail(f"missing {path.relative_to(REPO_ROOT)}")
        text = path.read_text(encoding="utf-8")
        if "§1f" not in text and "§1a" not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must reference structured-qa §1a/§1f")
        if re.search(r"prompt text", text, re.IGNORECASE):
            fail(f"{path.relative_to(REPO_ROOT)} must not instruct putting summary in prompt text")


def main() -> None:
    check_canonical_files()
    check_banned_phrases()
    check_preflight_qa_references()
    print("Structured Q&A shape checks passed.")


if __name__ == "__main__":
    main()
