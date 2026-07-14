#!/usr/bin/env python3
"""Brute template — slow correct reference reading multi-test stdin."""

from __future__ import annotations

import sys


def solve_case() -> str:
    raise NotImplementedError


def main() -> None:
    t = int(sys.stdin.readline())
    out: list[str] = []
    for _ in range(t):
        out.append(solve_case())
    sys.stdout.write("\n".join(out))
    if out:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
