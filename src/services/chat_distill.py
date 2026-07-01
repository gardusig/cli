"""Chat → R1 distill → categorize → GitHub issues per repo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.providers.deepseek import DeepSeekClient
from src.services.chat_session import ChatSession
from src.services.gh_service import GhService

_REPOS_CONFIG = Path(__file__).resolve().parents[2] / "config" / "chat" / "repos.yaml"

R1_SYSTEM = """You are an exhaustive idea extractor (DeepSeek R1 / reasoner role).
Read the full planning chat. List every theme, vague idea, risk, and cross-repo dependency.
Output JSON with keys:
- themes: [{id, title, description, vagueness: low|medium|high, repos_mentioned: []}]
- cross_repo_risks: [{description, source_repo, affected_repos: []}]
- open_questions: [string]
- raw_notes: string (long-form traversal)
Do not file issues yet — only extract and connect ideas."""

CATEGORIZE_SYSTEM = """You categorize planning output into GitHub actions per repository.
Each gardusig repo is SEPARATE — one parent epic per repo when themes apply.
Shared ideas get cross_repo_notes on each parent body.
Consider breaking changes (e.g. cli API change affecting yugioh workflows).

Output JSON:
{
  "repos": [
    {
      "repo": "gardusig/cli",
      "parent": {
        "title": "descriptive epic title (no step prefix)",
        "body": "markdown body with ## Context from chat",
        "priority": 1,
        "epic_slug": "hub-chat",
        "cross_repo_notes": ["..."]
      },
      "actions": [
        {"type": "comment", "issue_number": 69, "body": "## [cli] plan\\n..."},
        {"type": "create_child", "title": "1 — ...", "body": "...", "labels": ["issue-type:child", "epic:hub-chat"]}
      ]
    }
  ]
}
Use comment when an existing issue fits; create_parent + create_child for new work.
priority is 0-5 (1 = ship now). Include vague ideas as low-confidence children if useful."""


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

    open_issues_by_repo: dict[str, list[dict[str, Any]]] = {}
    for entry in load_repo_catalog():
        repo = entry["repo"]
        try:
            svc = GhService(repo=repo)
            open_issues_by_repo[repo] = svc.issue_list(state="open", limit=30)
        except Exception:
            open_issues_by_repo[repo] = []

    user = json.dumps(
        {
            "summary": session.summary(),
            "distill_r1": distill,
            "repos": load_repo_catalog(),
            "open_issues": {
                repo: [{"number": i["number"], "title": i["title"]} for i in issues]
                for repo, issues in open_issues_by_repo.items()
            },
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
    """Apply categorize JSON — create parents, children, comments."""
    results: list[dict[str, Any]] = []
    for block in plan.get("repos") or []:
        repo = str(block.get("repo", ""))
        if not repo:
            continue
        svc = GhService(repo=repo)
        parent_ref: dict[str, Any] | None = None
        parent_spec = block.get("parent")
        epic_slug = None
        if parent_spec:
            labels = [
                "issue-type:epic",
                f"epic:{parent_spec.get('epic_slug', 'chat-plan')}",
                f"priority:{parent_spec.get('priority', 2)}",
            ]
            body = str(parent_spec.get("body", ""))
            notes = parent_spec.get("cross_repo_notes") or []
            if notes:
                body += "\n\n## Cross-repo notes\n" + "\n".join(f"- {n}" for n in notes)
            if yes:
                parent = svc.issue_create(
                    title=str(parent_spec.get("title", "Chat plan epic")),
                    body=body,
                )
                svc.issue_edit(int(parent["number"]), add_labels=labels)
                parent_ref = parent
                epic_slug = parent_spec.get("epic_slug", "chat-plan")
                results.append({"repo": repo, "action": "create_parent", **parent})
            else:
                epic_slug = parent_spec.get("epic_slug", "chat-plan")
                results.append(
                    {
                        "repo": repo,
                        "action": "create_parent",
                        "dry_run": True,
                        "title": parent_spec.get("title"),
                    }
                )

        for action in block.get("actions") or []:
            kind = action.get("type")
            if kind == "comment" and action.get("issue_number"):
                num = int(action["issue_number"])
                body = str(action.get("body", ""))
                if yes:
                    svc.issue_comment(num, body=body)
                results.append({"repo": repo, "action": "comment", "number": num, "applied": yes})
            elif kind in {"create", "create_child"} and yes:
                labels = list(action.get("labels") or [])
                if epic_slug and "epic:" not in "".join(labels):
                    labels.append(f"epic:{epic_slug}")
                if "issue-type:child" not in labels:
                    labels.append("issue-type:child")
                created = svc.issue_create(
                    title=str(action.get("title", "Untitled")),
                    body=str(action.get("body", "")),
                    labels=labels,
                )
                results.append({"repo": repo, "action": "create_child", **created})
            elif kind in {"create", "create_child"}:
                results.append({"repo": repo, "action": "create_child", "dry_run": True, **action})
    return results


def pipeline_from_summary(
    summary: str,
    *,
    session_id: str = "workflow-import",
    run_distill: bool = True,
    client: DeepSeekClient | None = None,
) -> dict[str, Any]:
    """Import summary (e.g. from workflow_dispatch) and run distill + categorize."""
    session = ChatSession.create(session_id)
    session.set_summary(summary)
    session.append("user", f"[imported summary]\n{summary}")
    client = client or DeepSeekClient()
    distill: dict[str, Any] = {}
    if run_distill:
        distill = run_r1_distill(session, client)
    plan = run_categorize(session, distill=distill, client=client)
    return {"session_id": session.session_id, "distill": distill, "plan": plan}
