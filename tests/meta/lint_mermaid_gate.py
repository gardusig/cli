#!/usr/bin/env python3
"""Validate mermaid fences in markdown (invoked from scripts/pull-request/lint.sh)."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MERMAID_FENCE = re.compile(r"^```mermaid\s*$", re.MULTILINE)


def main() -> int:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        blocks = []
        lines = text.splitlines()
        index = 0
        while index < len(lines):
            if lines[index].strip() != "```mermaid":
                index += 1
                continue
            index += 1
            body: list[str] = []
            while index < len(lines) and lines[index].strip() != "```":
                body.append(lines[index])
                index += 1
            blocks.append("\n".join(body))
            index += 1
        for block_index, block in enumerate(blocks, start=1):
            with tempfile.TemporaryDirectory() as tmp:
                diagram = Path(tmp) / f"mermaid-{block_index}.mmd"
                diagram.write_text(block + "\n", encoding="utf-8")
                result = subprocess.run(
                    ["mmdc", "-i", str(diagram), "-o", str(Path(tmp) / "out.svg")],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    rel = path.relative_to(ROOT)
                    errors.append(f"{rel} mermaid block {block_index}: {result.stderr.strip()}")
    if errors:
        print("mermaid lint failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("mermaid ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
