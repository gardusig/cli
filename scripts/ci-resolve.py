#!/usr/bin/env python3
"""Resolve hub workflow job graph (was `cli pipeline config resolve`)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ci_runtime.runtime import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "config-resolve":
        sys.argv.insert(1, "config-resolve")
    main()
