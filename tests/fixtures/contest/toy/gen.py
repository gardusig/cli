#!/usr/bin/env python3
"""Toy generator: sum-of-array problem with small corner cases and large stress."""

from __future__ import annotations

import sys
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
sys.path.insert(0, str(_TEMPLATES))

from lib import Case, format_multi_test  # noqa: E402


def format_one(payload: dict) -> list[str]:
    values = payload["values"]
    return [str(len(values)), " ".join(map(str, values))]


def small_cases() -> list[Case]:
    return [
        Case("one", {"values": [7]}),
        Case("zeros", {"values": [0, 0, 0]}),
        Case("neg", {"values": [-3, 5, -2]}),
        Case("pair", {"values": [10, 20]}),
    ]


def large_cases() -> list[Case]:
    n = 45_000
    return [Case("stress", {"values": list(range(1, n + 1))})]


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"small", "large"}:
        print("usage: python gen.py small|large", file=sys.stderr)
        raise SystemExit(2)
    tier = sys.argv[1]
    cases = small_cases() if tier == "small" else large_cases()
    sys.stdout.write(format_multi_test(cases, format_one))


if __name__ == "__main__":
    main()
