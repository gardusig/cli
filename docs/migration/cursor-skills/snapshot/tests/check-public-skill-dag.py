#!/usr/bin/env python3
"""
Validate .cursor/tests/fixtures/public-skill-dag/graph.json:
  - required-edge subgraph is acyclic
  - optional edges are ignored for cycle detection
  - every public-skills.txt path appears exactly once on a node.skillPath
  - optional: warn on transitively redundant required edges
Emit: --emit-mermaid prints the Full public DAG block (flowchart TB) for docs/README.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[1]
_FIXTURE = _TESTS_DIR / "fixtures" / "public-skill-dag" / "graph.json"
_PUBLIC_SKILLS = _TESTS_DIR / "public-skills.txt"
_README = _REPO_ROOT / "docs" / "README.md"
_MARK_START = "<!-- public-skill-dag:mermaid:start -->"
_MARK_END = "<!-- public-skill-dag:mermaid:end -->"

# Mermaid node ids aligned with docs/README.md (historical shorthand where it differs from kebab-camel).
_MERMAID_ID_OVERRIDES: dict[str, str] = {
    "gh-issue-list": "ghIssueList",
    "gh-issue-backlog": "ghIssueBacklog",
    "gh-issue-next": "ghIssueNext",
    "gh-issue-labels": "ghIssueLabels",
    "gh-issue-execute": "ghIssuesExecute",
    "gh-issue-review": "ghIssueReview",
    "gh-issue-view": "ghIssueView",
    "gh-issue-create": "ghIssueCreate",
    "gh-issue-edit": "ghIssueEdit",
    "gh-issue-pick": "ghIssuePick",
    "gh-issue-delete-closed": "ghIssueDeleteClosed",
    "gh-issue-close": "ghIssueClose",
}


def _mermaid_id(node_id: str) -> str:
    if node_id in _MERMAID_ID_OVERRIDES:
        return _MERMAID_ID_OVERRIDES[node_id]
    parts = node_id.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:] if p)


def _mermaid_label(node: dict[str, Any]) -> str:
    raw = node.get("mermaidLabel") or node["id"]
    # Quote when mermaid would mis-parse (spaces, §, brackets, quotes).
    if any(c in raw for c in '§[]()"#') or " " in raw:
        return '"' + raw.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return raw


def _load_graph() -> dict[str, Any]:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError("graph.json: unsupported version")
    return data


def _required_adj(edges: list[dict[str, Any]], nodes: set[str]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for e in edges:
        if e.get("kind") != "required":
            continue
        u, v = e["from"], e["to"]
        adj[u].append(v)
    return adj


def _detect_cycle_kahn(adj: dict[str, list[str]], nodes: set[str]) -> bool:
    """True if required subgraph has a directed cycle."""
    indeg = {n: 0 for n in nodes}
    for u in nodes:
        for v in adj.get(u, []):
            indeg[v] += 1
    q: deque[str] = deque(sorted(n for n in nodes if indeg[n] == 0))
    seen = 0
    while q:
        u = q.popleft()
        seen += 1
        for v in adj.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return seen != len(nodes)


def _reachable_without_edge(
    adj: dict[str, list[str]], start: str, goal: str, skip_u: str, skip_v: str
) -> bool:
    """Is goal reachable from start if we remove edge skip_u -> skip_v (one copy)?"""
    q: deque[str] = deque([start])
    seen: set[str] = {start}
    while q:
        u = q.popleft()
        if u == goal:
            return True
        for v in adj[u]:
            if u == skip_u and v == skip_v:
                continue
            if v not in seen:
                seen.add(v)
                q.append(v)
    return False


def _transitive_redundant_required(
    edges: list[dict[str, Any]], nodes: set[str]
) -> list[tuple[str, str]]:
    req = [e for e in edges if e.get("kind") == "required"]
    adj_full: dict[str, list[str]] = defaultdict(list)
    for e in req:
        adj_full[e["from"]].append(e["to"])
    adj_full = {n: list(adj_full[n]) for n in nodes}  # ensure keys

    redundant: list[tuple[str, str]] = []
    for e in req:
        u, v = e["from"], e["to"]
        if _reachable_without_edge(adj_full, u, v, u, v):
            redundant.append((u, v))
    return redundant


def _validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes_raw = data.get("nodes") or []
    edges = data.get("edges") or []

    node_ids = {n["id"] for n in nodes_raw}
    for sg in data.get("subgraphs") or []:
        if "id" not in sg:
            errors.append("subgraph missing id")
        else:
            for key in ("mermaidBlockId", "mermaidTitle"):
                if key not in sg:
                    errors.append(f"subgraph {sg['id']!r} missing {key}")

    for n in nodes_raw:
        if "id" not in n:
            errors.append("node missing id")

    seen_paths: dict[str, str] = {}
    for n in nodes_raw:
        sp = n.get("skillPath")
        if not sp:
            continue
        nid = n["id"]
        if sp in seen_paths:
            errors.append(f"duplicate skillPath {sp!r} on {nid} and {seen_paths[sp]}")
        seen_paths[sp] = nid

    edge_keys: set[tuple[str, str, str]] = set()
    for i, e in enumerate(edges):
        for k in ("from", "to", "kind"):
            if k not in e:
                errors.append(f"edge[{i}] missing {k}")
                continue
        if e["from"] not in node_ids:
            errors.append(f"edge unknown from: {e['from']!r}")
        if e["to"] not in node_ids:
            errors.append(f"edge unknown to: {e['to']!r}")
        if e.get("kind") not in ("required", "optional"):
            errors.append(f"edge invalid kind: {e!r}")
        key = (e["from"], e["to"], e.get("kind", ""))
        if key in edge_keys:
            errors.append(f"duplicate edge: {key}")
        edge_keys.add(key)

    nodes = set(node_ids)
    req_adj = _required_adj(edges, nodes)
    if _detect_cycle_kahn(req_adj, nodes):
        errors.append("required-edge subgraph contains a cycle")

    listed = {Path(p.strip()).as_posix() for p in _PUBLIC_SKILLS.read_text(encoding="utf-8").splitlines() if p.strip()}
    graphed: set[str] = set()
    for n in nodes_raw:
        sp = n.get("skillPath")
        if sp:
            graphed.add(Path(sp).as_posix())

    missing = sorted(listed - graphed)
    extra = sorted(graphed - listed)
    for p in missing:
        errors.append(f"public-skill path not in graph nodes: {p}")
    for p in extra:
        errors.append(f"graph skillPath not in public-skills.txt: {p}")

    return errors


def _emit_mermaid(data: dict[str, Any]) -> str:
    """Emit mermaid from graph.json nodes, subgraphs, and edges."""
    nodes = {n["id"]: n for n in data["nodes"]}

    def mid(nid: str) -> str:
        return _mermaid_id(nid)

    def lab(nid: str) -> str:
        return _mermaid_label(nodes[nid])

    lines: list[str] = ["flowchart TB", ""]

    for sg in data.get("subgraphs") or []:
        sg_id = sg["id"]
        lines.append(f"  subgraph {sg['mermaidBlockId']} [{sg['mermaidTitle']}]")
        for n in data["nodes"]:
            if n.get("subgraph") == sg_id:
                lines.append(f"    {mid(n['id'])}[{lab(n['id'])}]")
        lines.append("  end")
        lines.append("")

    for e in data.get("edges") or []:
        op = "-->" if e.get("kind") == "required" else "-.->"
        lines.append(f"  {mid(e['from'])} {op} {mid(e['to'])}")

    lines.append("")
    return "\n".join(lines)


def _emit_covers_all_edges(emit: str, data: dict[str, Any]) -> list[str]:
    """Ensure every graph.json edge appears in emitted mermaid (layout is hand-ordered)."""
    missing: list[str] = []
    for e in data.get("edges") or []:
        u, v, k = e["from"], e["to"], e.get("kind", "")
        op = re.escape("-->" if k == "required" else "-.->")
        a = re.escape(_mermaid_id(u))
        b = re.escape(_mermaid_id(v))
        pat = re.compile(
            a + r"(?:\[[^\]]*\])?" + r"\s*" + op + r"\s*" + b + r"(?:\[[^\]]*\])?",
            re.MULTILINE,
        )
        if not pat.search(emit):
            missing.append(f"edge not found in emitted mermaid: {u!r} -> {v!r} ({k})")
    return missing


def _readme_mermaid_block(readme_text: str) -> str | None:
    if _MARK_START not in readme_text or _MARK_END not in readme_text:
        return None
    a = readme_text.index(_MARK_START) + len(_MARK_START)
    b = readme_text.index(_MARK_END)
    inner = readme_text[a:b].strip()
    if inner.startswith("```mermaid"):
        inner = inner[len("```mermaid") :].lstrip("\n")
    if inner.endswith("```"):
        inner = inner[: inner.rindex("```")].rstrip()
    return inner.strip()


def _write_readme_mermaid(readme_path: Path, mermaid_body: str) -> None:
    text = readme_path.read_text(encoding="utf-8")
    if _MARK_START not in text or _MARK_END not in text:
        raise ValueError(f"README missing markers {_MARK_START!r} / {_MARK_END!r}")
    a = text.index(_MARK_START)
    b = text.index(_MARK_END) + len(_MARK_END)
    block = (
        f"{_MARK_START}\n"
        "```mermaid\n"
        f"{mermaid_body.rstrip()}\n"
        "```\n"
        f"{_MARK_END}"
    )
    new_text = text[:a] + block + text[b:]
    readme_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--emit-mermaid",
        action="store_true",
        help="Print flowchart TB (full public DAG) to stdout",
    )
    ap.add_argument(
        "--verify-readme",
        action="store_true",
        help=f"Assert docs/README.md mermaid between markers matches fixture emission",
    )
    ap.add_argument(
        "--write-readme",
        action="store_true",
        help=f"Rewrite docs/README.md mermaid block from fixture (uses {_MARK_START})",
    )
    args = ap.parse_args()

    try:
        data = _load_graph()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.emit_mermaid:
        emit = _emit_mermaid(data)
        miss = _emit_covers_all_edges(emit, data)
        for m in miss:
            print(f"ERROR: {m}", file=sys.stderr)
        if miss:
            return 1
        print(emit, end="")
        return 0

    if args.write_readme:
        emit = _emit_mermaid(data)
        miss = _emit_covers_all_edges(emit, data)
        for m in miss:
            print(f"ERROR: {m}", file=sys.stderr)
        if miss:
            return 1
        _write_readme_mermaid(_README, emit)
        print(f"Wrote mermaid block to {_README}")
        return 0

    if args.verify_readme:
        emit = _emit_mermaid(data)
        miss = _emit_covers_all_edges(emit, data)
        for m in miss:
            print(f"ERROR: {m}", file=sys.stderr)
        if miss:
            return 1
        readme = _README.read_text(encoding="utf-8")
        block = _readme_mermaid_block(readme)
        if block is None:
            print("ERROR: could not extract README mermaid between markers", file=sys.stderr)
            return 1
        n_emit = "\n".join(line.rstrip() for line in emit.strip().splitlines())
        n_block = "\n".join(line.rstrip() for line in block.splitlines())
        if n_emit != n_block:
            print("ERROR: README mermaid block differs from fixture emission", file=sys.stderr)
            return 1
        print("README public-skill-dag mermaid: OK")
        return 0

    errors = _validate(data)
    redundant = _transitive_redundant_required(data["edges"], {n["id"] for n in data["nodes"]})
    for u, v in redundant:
        print(f"WARNING: transitively redundant required edge {u!r} -> {v!r}", file=sys.stderr)

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    emit = _emit_mermaid(data)
    miss = _emit_covers_all_edges(emit, data)
    for m in miss:
        errors.append(m)

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    readme = _README.read_text(encoding="utf-8")
    if _MARK_START in readme and _MARK_END in readme:
        block = _readme_mermaid_block(readme)
        if block is not None:
            n_emit = "\n".join(line.rstrip() for line in emit.strip().splitlines())
            n_block = "\n".join(line.rstrip() for line in block.splitlines())
            if n_emit != n_block:
                print(
                    "ERROR: README mermaid drift; run: python3 .cursor/tests/check-public-skill-dag.py --write-readme",
                    file=sys.stderr,
                )
                return 1

    print("public-skill-dag: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
