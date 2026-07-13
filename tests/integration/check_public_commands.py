#!/usr/bin/env python3
"""Run read-only integration smoke against the installed `cli` binary."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts" / "pull-request" / "integration-smoke.sh"


def main() -> int:
    if not SMOKE.is_file():
        print(f"missing smoke script: {SMOKE}", file=sys.stderr)
        return 1
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env.setdefault("CLI_CONFIG_DIR", str(ROOT / "config"))
    env.setdefault("CLI_PROFILE", "test")
    result = subprocess.run(["bash", str(SMOKE)], cwd=ROOT, env=env, check=False)
    if result.returncode != 0:
        return result.returncode
    print("Public command integration passed (integration-smoke.sh).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
