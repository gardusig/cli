#!/usr/bin/env python3
"""Toy brute: O(n^2) sum via nested loops (TLEs on large tier)."""

from __future__ import annotations

import sys


def solve_case() -> str:
    n = int(sys.stdin.readline())
    arr = list(map(int, sys.stdin.readline().split()))
    total = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                total += arr[i]
    return str(total)


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
