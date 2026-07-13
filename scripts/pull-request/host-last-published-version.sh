#!/usr/bin/env bash
# Host-only helper: print the latest version published on PyPI (empty when none yet).
set -euo pipefail

python3 - <<'PY'
import json
import sys
import urllib.error
import urllib.request

PACKAGE = "gardusig-cli"
URL = f"https://pypi.org/pypi/{PACKAGE}/json"


def parse(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.strip().lstrip("v").split("."):
        digits = ""
        for char in piece:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits or "0"))
    return tuple(parts)


try:
    with urllib.request.urlopen(URL, timeout=20) as response:
        data = json.load(response)
except urllib.error.HTTPError as exc:
    if exc.code == 404:
        sys.exit(0)
    raise

releases = data.get("releases") or {}
versions = [version for version, files in releases.items() if files]
if not versions:
    sys.exit(0)

print(max(versions, key=parse))
PY
