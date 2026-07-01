#!/usr/bin/env python3
"""Fail when the same gh/git command appears in bash fences under multiple read/write skills."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
READ_WRITE = (
    REPO_ROOT / "skills" / "internal" / "read",
    REPO_ROOT / "skills" / "internal" / "write",
)

# Generic ref resolution appears in workflow sync and tag target checks (different callers).
ALLOW_DUPLICATE_KEYS = frozenset({
    'git rev-parse "$VAR"',
    'git show "$VAR"',
})

BASH_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
# gh search issues is two tokens; gh api and gh label are separate families.
GH_PREFIX = re.compile(
    r"^\s*gh\s+(?:(?:api|auth|issue|pr|repo|label)\b|search\s+issues)\b[^\n]*",
    re.MULTILINE,
)
GIT_PREFIX = re.compile(
    r"^\s*git(?:\s+-C\s+[^\s]+)?\s+(?:add|branch|checkout|cherry-pick|clean|commit|diff|fetch|merge|merge-base|push|rebase|reset|rev-parse|revert|stash|status|tag)\b[^\n]*",
    re.MULTILINE,
)


def normalize(line: str) -> str:
    s = line.strip()
    s = re.sub(r"\s+-C\s+[\"']?\$TOP[\"']?", "", s)
    s = re.sub(r"\s+-C\s+[^\s]+", "", s)
    # Keep distinguishing git subcommand modifiers before stripping other flags.
    fetch_extra = ""
    if re.search(r"\bgit\s+fetch\b", s) and "--tags" in s:
        fetch_extra = " --tags"
    rev_extra = ""
    m = re.search(r"\bgit\s+rev-parse\b(.*)$", s)
    if m:
        tail = m.group(1)
        for token in (
            "--is-inside-work-tree",
            "--show-toplevel",
            "-q",
            "--verify",
        ):
            if token in tail:
                rev_extra += f" {token}"
    s = re.sub(r"\s+--[^\s]+", "", s)
    s = re.sub(r"\s+", " ", s)
    if fetch_extra:
        s = s.replace("git fetch", "git fetch" + fetch_extra, 1)
    if rev_extra and "git rev-parse" in s:
        s = s.replace("git rev-parse", "git rev-parse" + rev_extra, 1)
    s = re.sub(r"<[^>]+>", "<>", s)
    s = re.sub(r"\$[A-Z_]+", "$VAR", s)
    s = re.sub(r"\d+", "N", s)
    return s


def command_keys(block: str) -> set[str]:
    keys: set[str] = set()
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("gh "):
            keys.add(normalize(line))
        elif "git" in line and re.match(r"git(?:\s+-C\s+[^\s]+)?\s+", line):
            keys.add(normalize(line))
    return keys


def iter_skill_files() -> list[Path]:
    files: list[Path] = []
    for root in READ_WRITE:
        files.extend(sorted(root.rglob("SKILL.md")))
    return files


def main() -> int:
    owners: dict[str, list[str]] = defaultdict(list)

    for path in iter_skill_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for match in BASH_FENCE.finditer(text):
            for key in command_keys(match.group(1)):
                owners[key].append(rel)

    duplicates = {
        k: sorted(set(v))
        for k, v in owners.items()
        if len(set(v)) > 1 and k not in ALLOW_DUPLICATE_KEYS
    }

    if duplicates:
        print("FAIL: duplicate gh/git commands in read/write bash fences:\n", file=sys.stderr)
        for key in sorted(duplicates):
            print(f"  {key}", file=sys.stderr)
            for f in duplicates[key]:
                print(f"    - {f}", file=sys.stderr)
        return 1

    print(f"OK: {len(owners)} distinct command keys, no cross-skill duplicates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
