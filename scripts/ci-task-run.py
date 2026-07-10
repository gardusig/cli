#!/usr/bin/env python3
"""Run a resolved hub task action (was `cli pipeline task run`)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ci_runtime.runtime import run_task_action


def main() -> None:
    parser = argparse.ArgumentParser(prog="scripts/ci-task-run.py")
    parser.add_argument("--command-json", required=True)
    parser.add_argument("--env-json", default="{}")
    parser.add_argument("--repo-dir", type=Path, required=True)
    args = parser.parse_args()
    run_task_action(args)


if __name__ == "__main__":
    main()
