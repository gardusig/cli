#!/usr/bin/env python3
"""Notion task-pair integration (delegates to unified API integration runner)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/integration/check_api_integration.py")],
        cwd=ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
