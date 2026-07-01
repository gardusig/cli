#!/usr/bin/env python3
"""
Issue #45: public SKILL.md routing (folded description tokens) + Before batch structure.

Reads public-skills.txt and fixtures/public-skill-routing-tokens.json in this directory.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parents[1]
REGISTRY = _TESTS_DIR / "public-skills.txt"
MANIFEST = _TESTS_DIR / "fixtures" / "public-skill-routing-tokens.json"

_AT_MENTION = re.compile(r"@([a-z0-9-]+)\b", re.IGNORECASE)
_LIBRARY_TOKEN = re.compile(
    r"\b(?:read|write)-[a-z0-9]+-[a-z0-9-]+\b", re.IGNORECASE
)
_INTERNAL_LINK = re.compile(
    r"\]\([^)]*\bskills/(?:read|write)/[^)]+\)", re.IGNORECASE
)
_BEFORE_HEADING = re.compile(r"^##\s+before\s+batch\b", re.IGNORECASE | re.MULTILINE)
_REQUIRED_INTERNAL_HEADING = re.compile(
    r"^##\s+required\s+internal\s+skills\b", re.IGNORECASE | re.MULTILINE
)
_RECOMMENDED_NEXT_HEADING = re.compile(
    r"^##\s+recommended\s+next\s+steps\b", re.IGNORECASE | re.MULTILINE
)
_FOLLOWUP_QA_HEADING = re.compile(
    r"^##\s+follow-up\s+q&a\s+\(optional\)", re.IGNORECASE | re.MULTILINE
)
_VERIFICATION_HEADING = re.compile(
    r"^##\s+verification\b", re.IGNORECASE | re.MULTILINE
)
_VERIFICATION_CHECKBOX = re.compile(r"^\s*-\s+\[\s\]\s+", re.MULTILINE)
# Runnable CLI in backticks (or bash fences) — public skills delegate to read-* / write-* libraries.
_INLINE_GIT_CMD = re.compile(r"`git\s+[a-z]", re.IGNORECASE)
_INLINE_GH_CMD = re.compile(
    r"`gh\s+(?:issue|pr|project|api)\s+[a-z]", re.IGNORECASE
)
_SHELL_FENCE = re.compile(r"```(?:bash|sh)\b", re.IGNORECASE)


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    fm = text[4:end]
    body = text[end + 5 :]
    return fm, body


def _parse_simple_key(fm: str, key: str) -> str | None:
    for line in fm.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def _parse_folded_description(fm: str) -> str:
    lines = fm.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("description:"):
            rest = line.split(":", 1)[1].strip()
            if rest in (">-", ">", "|", "|-") or rest.startswith((">-", ">", "|")):
                i += 1
                while i < len(lines):
                    cont = lines[i]
                    if cont.startswith((" ", "\t")):
                        out.append(cont.strip())
                        i += 1
                        continue
                    break
                break
            else:
                out.append(rest)
            break
        i += 1
    return " ".join(out)


def _norm_ws(s: str) -> str:
    return " ".join(s.split())


def _first_sentence(s: str) -> str:
    s = _norm_ws(s)
    m = re.search(r"\.\s+", s)
    if m:
        return s[: m.start() + 1].strip()
    return s.strip()


def _at_to_canonical(handle: str, public_names: set[str]) -> str | None:
    h = handle.lower().lstrip("@")
    if h in public_names:
        return h
    if h.startswith("gh-issue-") and h != "gh-issue":
        cand = "gh-issue-" + h[len("gh-issue-") :]
        if cand in public_names:
            return cand
    return None


def _extract_section(body: str, heading_rx: re.Pattern[str]) -> str | None:
    m = heading_rx.search(body)
    if not m:
        return None
    start = m.end()
    rest = body[start:]
    m2 = re.search(r"^##\s+", rest, re.MULTILINE)
    if m2:
        return rest[: m2.start()]
    return rest


def _extract_before_batch_section(body: str) -> str | None:
    return _extract_section(body, _BEFORE_HEADING)


def _heading_index(body: str, heading_rx: re.Pattern[str]) -> int | None:
    m = heading_rx.search(body)
    return m.start() if m else None


def _before_batch_has_library(text: str) -> bool:
    if _LIBRARY_TOKEN.search(text):
        return True
    if _INTERNAL_LINK.search(text):
        return True
    if re.search(r"skills/(?:read|write)/", text, re.IGNORECASE):
        return True
    return False


def _peer_public_mentions(
    before_text: str, self_name: str, public_names: set[str]
) -> list[str]:
    found: list[str] = []
    for m in _AT_MENTION.finditer(before_text):
        canon = _at_to_canonical(m.group(1), public_names)
        if canon and canon != self_name:
            found.append(canon)
    return found


def _public_body_inline_cli_violations(body: str) -> list[str]:
    """Return human-readable violation labels for banned inline git/gh command shapes."""
    hits: list[str] = []
    if _INLINE_GIT_CMD.search(body):
        hits.append("`git <subcommand>`")
    if _INLINE_GH_CMD.search(body):
        hits.append("`gh issue|pr|project|api <...>`")
    if _SHELL_FENCE.search(body):
        hits.append("```bash/```sh fence")
    return hits


def main() -> int:
    public_paths: list[str] = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            public_paths.append(line)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    skills_cfg: dict = manifest["skills"]
    pairs: list[list[str]] = manifest.get("first_sentence_must_differ", [])

    public_names: set[str] = set()
    path_by_name: dict[str, Path] = {}
    desc_by_name: dict[str, str] = {}
    body_by_name: dict[str, str] = {}

    for rel in public_paths:
        path = REPO_ROOT / rel
        if not path.is_file():
            print(f"FAIL: missing file {rel}", file=sys.stderr)
            return 1
        raw = path.read_text(encoding="utf-8")
        fm, body = _split_frontmatter(raw)
        name = _parse_simple_key(fm, "name")
        if not name:
            print(f"FAIL: missing name: in {rel}", file=sys.stderr)
            return 1
        desc = _parse_folded_description(fm)
        if not desc.strip():
            print(f"FAIL: empty folded description in {rel}", file=sys.stderr)
            return 1
        public_names.add(name)
        path_by_name[name] = path
        desc_by_name[name] = desc
        body_by_name[name] = body

    if set(skills_cfg) != public_names:
        missing = sorted(public_names - set(skills_cfg))
        extra = sorted(set(skills_cfg) - public_names)
        if missing:
            print(f"FAIL: manifest missing entries: {missing}", file=sys.stderr)
        if extra:
            print(f"FAIL: manifest unknown entries: {extra}", file=sys.stderr)
        return 1

    errors = 0
    dnorm = {n: _norm_ws(d).lower() for n, d in desc_by_name.items()}

    for name, cfg in skills_cfg.items():
        req: list[str] = cfg.get("require_all", [])
        d = dnorm[name]
        for token in req:
            if token.lower() not in d:
                print(
                    f"FAIL: {name} ({path_by_name[name].relative_to(REPO_ROOT)}): "
                    f"description missing required substring {token!r}",
                    file=sys.stderr,
                )
                errors += 1

    for a, b in pairs:
        sa = _first_sentence(desc_by_name[a]).lower()
        sb = _first_sentence(desc_by_name[b]).lower()
        if sa == sb:
            print(
                f"FAIL: first description sentence must differ for {a!r} vs {b!r} "
                f"(both normalize to {sa!r})",
                file=sys.stderr,
            )
            errors += 1

    for name in sorted(public_names):
        cfg = skills_cfg[name]
        if cfg.get("before_batch_exempt"):
            continue
        body = body_by_name[name]
        before = _extract_before_batch_section(body)
        rel = path_by_name[name].relative_to(REPO_ROOT)
        if before is None:
            print(f"FAIL: {name} ({rel}): missing ## Before batch section", file=sys.stderr)
            errors += 1
            continue

        peers = _peer_public_mentions(before, name, public_names)
        if not peers and not cfg.get("before_batch_no_peer_public"):
            print(
                f"FAIL: {name} ({rel}): Before batch needs @ mention of another public skill "
                f"(or set before_batch_no_peer_public in manifest with rationale)",
                file=sys.stderr,
            )
            errors += 1
        if _before_batch_has_library(before):
            print(
                f"FAIL: {name} ({rel}): Before batch must list public @ skill prerequisites only; "
                f"move read-*/write-* references to ## Required internal skills",
                file=sys.stderr,
            )
            errors += 1

        required = _extract_section(body, _REQUIRED_INTERNAL_HEADING)
        if required is None:
            print(
                f"FAIL: {name} ({rel}): missing ## Required internal skills section",
                file=sys.stderr,
            )
            errors += 1
        elif not _before_batch_has_library(required):
            print(
                f"FAIL: {name} ({rel}): Required internal skills must list read-*/write-* "
                f"libraries",
                file=sys.stderr,
            )
            errors += 1

        ib = _heading_index(body, _BEFORE_HEADING)
        ir = _heading_index(body, _REQUIRED_INTERNAL_HEADING)
        iv = _heading_index(body, _VERIFICATION_HEADING)
        inext = _heading_index(body, _RECOMMENDED_NEXT_HEADING)
        if ib is not None and ir is not None and ir < ib:
            print(
                f"FAIL: {name} ({rel}): ## Required internal skills must follow ## Before batch",
                file=sys.stderr,
            )
            errors += 1
        if ir is not None and iv is not None and iv < ir:
            print(
                f"FAIL: {name} ({rel}): ## Verification must follow ## Required internal skills",
                file=sys.stderr,
            )
            errors += 1
        if iv is not None and inext is not None and inext < iv:
            print(
                f"FAIL: {name} ({rel}): ## Recommended next steps must follow ## Verification",
                file=sys.stderr,
            )
            errors += 1

        if _FOLLOWUP_QA_HEADING.search(body):
            print(
                f"FAIL: {name} ({rel}): use ## Recommended next steps, not "
                f"## Follow-up Q&A (optional)",
                file=sys.stderr,
            )
            errors += 1

        rec = _extract_section(body, _RECOMMENDED_NEXT_HEADING)
        if rec is None:
            print(
                f"FAIL: {name} ({rel}): missing ## Recommended next steps section",
                file=sys.stderr,
            )
            errors += 1
        elif "read-skill-suggestions" not in rec.lower():
            print(
                f"FAIL: {name} ({rel}): Recommended next steps must reference "
                f"read-skill-suggestions",
                file=sys.stderr,
            )
            errors += 1
        elif "`skip=false`" not in rec or "`skip=true`" not in rec:
            print(
                f"FAIL: {name} ({rel}): Recommended next steps must define explicit "
                f"`skip=false` (root) and `skip=true` (nested child) behavior",
                file=sys.stderr,
            )
            errors += 1

        if not cfg.get("allow_inline_cli"):
            for label in _public_body_inline_cli_violations(body):
                print(
                    f"FAIL: {name} ({rel}): public skill must not embed runnable CLI "
                    f"({label}); use read-* / write-* block names",
                    file=sys.stderr,
                )
                errors += 1

        if not cfg.get("verification_exempt"):
            if not _VERIFICATION_HEADING.search(body):
                print(
                    f"FAIL: {name} ({rel}): missing ## Verification section",
                    file=sys.stderr,
                )
                errors += 1
            else:
                m = _VERIFICATION_HEADING.search(body)
                after = body[m.end() :] if m else ""
                m2 = re.search(r"^##\s+", after, re.MULTILINE)
                vsec = after[: m2.start()] if m2 else after
                boxes = _VERIFICATION_CHECKBOX.findall(vsec)
                if len(boxes) < 2:
                    print(
                        f"FAIL: {name} ({rel}): ## Verification needs at least 2 "
                        f"- [ ] checklist items (found {len(boxes)})",
                        file=sys.stderr,
                    )
                    errors += 1

    if errors:
        return 1
    print("Public skill routing + Before batch checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
