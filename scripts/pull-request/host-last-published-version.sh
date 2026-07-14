#!/usr/bin/env bash
# Host-only helper: print the greatest version on PyPI or TestPyPI (empty when none yet).
set -euo pipefail

python3 - <<'PY'
import json
import sys
import urllib.error
import urllib.request

PACKAGE = "gardusig-cli"
INDEXES = (
    ("PyPI", f"https://pypi.org/pypi/{PACKAGE}/json"),
    ("TestPyPI", f"https://test.pypi.org/pypi/{PACKAGE}/json"),
)


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


def latest_from_index(url: str) -> str | None:
    with urllib.request.urlopen(url, timeout=20) as response:
        data = json.load(response)
    releases = data.get("releases") or {}
    versions = [version for version, files in releases.items() if files]
    if not versions:
        return None
    return max(versions, key=parse)


best: str | None = None
errors: list[str] = []
for label, url in INDEXES:
    try:
        candidate = latest_from_index(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            continue
        errors.append(f"{label}: HTTP {exc.code}")
        continue
    except urllib.error.URLError as exc:
        errors.append(f"{label}: {exc.reason}")
        continue
    if candidate is None:
        continue
    if best is None or parse(candidate) > parse(best):
        best = candidate

if best:
    print(best)
elif errors:
    raise SystemExit("; ".join(errors))
PY
