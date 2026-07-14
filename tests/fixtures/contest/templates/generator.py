#!/usr/bin/env python3
"""Generator template — copy and implement small_cases() + large_cases().

Contract:
  small_cases() -> list[Case]   # corner cases, tiny inputs
  large_cases() -> list[Case]   # stress inputs (brute should TLE)
  format_one(payload) -> list[str]

Run:
  python gen.py small
  python gen.py large
"""

from __future__ import annotations

import sys

from lib import Case, format_multi_test


def format_one(payload: dict) -> list[str]:
    raise NotImplementedError


def small_cases() -> list[Case]:
    return [Case("sample", {})]


def large_cases() -> list[Case]:
    return [Case("stress", {})]


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"small", "large"}:
        print("usage: python gen.py small|large", file=sys.stderr)
        raise SystemExit(2)
    tier = sys.argv[1]
    cases = small_cases() if tier == "small" else large_cases()
    sys.stdout.write(format_multi_test(cases, format_one))


if __name__ == "__main__":
    main()
