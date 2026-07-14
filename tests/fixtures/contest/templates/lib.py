"""Shared helpers for contest input generators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class Case:
    name: str
    payload: object


def format_multi_test(
    cases: Sequence[Case],
    format_one: Callable[[object], list[str]],
) -> str:
    """Wrap single-case payloads in a multi-test batch (T on first line)."""
    lines = [str(len(cases))]
    for case in cases:
        lines.extend(format_one(case.payload))
    return "\n".join(lines) + "\n"
