"""Text normalization and comparison for contest outputs."""

from __future__ import annotations

import difflib


def normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def compare_text(expected: str, actual: str) -> bool:
    return normalize_text(expected) == normalize_text(actual)


def unified_diff(expected: str, actual: str, *, context: int = 3) -> str:
    exp_lines = normalize_text(expected).splitlines()
    act_lines = normalize_text(actual).splitlines()
    diff = difflib.unified_diff(
        exp_lines,
        act_lines,
        fromfile="brute",
        tofile="fast",
        lineterm="",
        n=context,
    )
    return "\n".join(diff)
