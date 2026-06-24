#!/usr/bin/env python3
"""Run all API docker integration tests (isolated fixtures, mocked remotes)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    from gardusig_cli.integration.workspaces import INTEGRATION_TEST_MODULES

    args = [sys.executable, "-m", "pytest", "-q", "--no-cov"]
    for mod in INTEGRATION_TEST_MODULES:
        path = mod.replace(".", "/") + ".py"
        args.append(path)

    result = subprocess.run(args, cwd=ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
