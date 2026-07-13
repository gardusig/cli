"""Chat → R1 distill → categorize (local artifacts only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.providers.deepseek import DeepSeekClient
from src.services.chat_session import ChatSession

_REPOS_CONFIG = Path(__file__).resolve().parents[2] / "config" / "chat" / "repos.yaml"

R1_SYSTEM = """You are an exhaustive idea extractor (DeepSeek R1 / reasoner role).
Read the full planning chat. List every theme, vague idea, risk, and dependency.
Output JSON with keys:
- themes: [{id, title, description, vagueness: low|medium|high, repos_mentioned: []}]
- cross_repo_risks: [{description, source_repo, affected_repos: []}]
- open_questions: [string]
- raw_notes: string (long-form traversal)
Do not file issues yet — only extract and connect ideas."""

CATEGORIZE_SYSTEM = """You categorize planning output into structured actions per repository theme.
Output JSON:
{
  "repos": [
    {
      "repo": "local/repo-name",
      "parent": {
        "title": "descriptive epic title",
        "body": "markdown body with ## Context from chat",
        "priority": 1,
        "epic_slug": "chat-plan",
        "cross_repo_notes": ["..."]
      },
      "actions": [
        {"type": "create_child", "title": "1 — ...", "body": "...", "labels": ["issue-type:child"]}
      ]
    }
  ]
}
Use priority 0-5 (1 = ship now). Include vague ideas as low-confidence children if useful."""


def load_repo_catalog() -> list[dict[str, str]]:
    if not _REPOS_CONFIG.is_file():
        return []
    data = yaml.safe_load(_REPOS_CONFIG.read_text(encoding="utf-8")) or {}
    owner = data.get("owner", "gardusig")
    return [
        {"repo": f"{owner}/{r['name']}", "description": r.get("description", "")}
        for r in data.get("repos") or []
    ]


def run_r1_distill(session: ChatSession, client: DeepSeekClient | None = None) -> dict[str, Any]:
    client = client or DeepSeekClient()
    transcript = session.transcript_text()
    summary = session.summary()
    user = (
        f"ROLLING SUMMARY:\n{summary}\n\n"
        f"FULL TRANSCRIPT:\n{transcript}\n\n"
        f"KNOWN REPOS:\n{json.dumps(load_repo_catalog(), indent=2)}"
    )
    raw = client.complete(
        [{"role": "system", "content": R1_SYSTEM}, {"role": "user", "content": user}],
        role="reason",
        temperature=0.2,
        json_mode=True,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"raw_notes": raw, "themes": [], "cross_repo_risks": [], "open_questions": []}
    path = session.artifact_path("distill-r1.json")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def run_categorize(
    session: ChatSession,
    *,
    distill: dict[str, Any] | None = None,
    client: DeepSeekClient | None = None,
) -> dict[str, Any]:
    client = client or DeepSeekClient()
    distill = distill or {}
    distill_path = session.artifact_path("distill-r1.json")
    if not distill and distill_path.is_file():
        distill = json.loads(distill_path.read_text(encoding="utf-8"))

    user = json.dumps(
        {
            "summary": session.summary(),
            "distill_r1": distill,
            "repos": load_repo_catalog(),
            "open_issues": {},
        },
        indent=2,
    )
    raw = client.complete(
        [{"role": "system", "content": CATEGORIZE_SYSTEM}, {"role": "user", "content": user}],
        role="categorize",
        temperature=0.2,
        json_mode=True,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"repos": [], "parse_error": raw}
    path = session.artifact_path("categorize.json")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def apply_categorize_plan(plan: dict[str, Any], *, yes: bool = False) -> list[dict[str, Any]]:
    """Return a dry-run summary of categorize JSON (no remote issue writes)."""
    results: list[dict[str, Any]] = []
    for block in plan.get("repos") or []:
        repo = str(block.get("repo", ""))
        if not repo:
            continue
        parent_spec = block.get("parent")
        if parent_spec:
            results.append(
                {
                    "repo": repo,
                    "action": "create_parent",
                    "dry_run": not yes,
                    "title": parent_spec.get("title"),
                }
            )
        for action in block.get("actions") or []:
            kind = action.get("type")
            if kind in {"create", "create_child", "comment"}:
                results.append({"repo": repo, "action": kind, "dry_run": not yes, **action})
    return results


def pipeline_from_summary(
    summary: str,
    *,
    session_id: str = "workflow-import",
    run_distill: bool = True,
    client: DeepSeekClient | None = None,
) -> dict[str, Any]:
    """Import summary and run distill + categorize."""
    session = ChatSession.create(session_id)
    session.set_summary(summary)
    session.append("user", f"[imported summary]\n{summary}")
    client = client or DeepSeekClient()
    distill: dict[str, Any] = {}
    if run_distill:
        distill = run_r1_distill(session, client)
    plan = run_categorize(session, distill=distill, client=client)
    return {"session_id": session.session_id, "distill": distill, "plan": plan}
