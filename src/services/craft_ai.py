"""AI prompts for craft/review — DeepSeek chat / reason / categorize roles."""

from __future__ import annotations

import json
from typing import Any, Literal

from src.providers.deepseek import DeepSeekClient, Role

CraftPhase = Literal[
    "issue_review",
    "issue_dedupe",
    "issue_ship",
    "issue_plan",
    "issue_execute",
    "pr_body",
    "pr_review",
    "code_guidance",
]

_ROLE: dict[CraftPhase, Role] = {
    "issue_review": "reason",
    "issue_dedupe": "categorize",
    "issue_ship": "categorize",
    "issue_plan": "reason",
    "issue_execute": "reason",
    "pr_body": "chat",
    "pr_review": "reason",
    "code_guidance": "reason",
}

_ISSUE_BODY_SECTIONS = """## Context
## Problem
## Acceptance
## Execution
(next: `cli craft execute` or `cli craft pr`)"""

_ISSUE_REVIEW_SYSTEM = f"""You reshape GitHub issues (read-only). Compare target issue to open peers.
Deliver markdown with sections:
## Summary
## Overlap map (peer #n — why related or distinct)
## Gaps (missing acceptance, vague scope, risks)
## Proposed reshape (title + body draft using sections:
{_ISSUE_BODY_SECTIONS})
## Verdict (ready_to_execute | needs_reshape | likely_duplicate)
Do not mutate GitHub — user applies via `cli craft issue`."""

_ISSUE_DEDUPE_SYSTEM = """Compare a candidate issue (title + summary) to open issues inventory.
Output JSON only:
{
  "verdict": "safe_to_create" | "likely_duplicate" | "ambiguous",
  "duplicate_number": null or int,
  "reason": "one line",
  "peer_overlaps": [{"number": int, "reason": "..."}]
}"""

_ISSUE_SHIP_SYSTEM = f"""Craft a GitHub issue from user intent. Output JSON:
{{
  "title": "step — short name OR epic title",
  "body": "markdown with {_ISSUE_BODY_SECTIONS.replace(chr(10), ' ')}",
  "labels": ["issue-type:child|epic", "epic:slug", "priority:N"],
  "action": "create" | "edit",
  "edit_number": null or int
}}
Respect dedupe verdict when provided."""

_ISSUE_PLAN_SYSTEM = """You plan implementation for a GitHub issue (DeepSeek reasoner).
Output markdown plan with:
## Goal
## Checkpoints (numbered, each with verification command or artifact)
## Risks
## Out of scope
Keep checkpoints executable in a headless CI environment when possible."""

_ISSUE_EXECUTE_SYSTEM = """You execute an approved issue plan checkpoint-by-checkpoint.
For each checkpoint output markdown:
## Checkpoint N — status (done|blocked|skipped)
Evidence (command output summary or file paths)
Then ## Handoff: `cli craft pr` when all done, or blocker description."""

_PR_BODY_SYSTEM = """Write a concise GitHub PR body in markdown:
## Summary
## Linked issues (#n)
## Test plan
## Notes
No merge instructions — merge happens in GitHub UI only."""

_PR_REVIEW_SYSTEM = """Review a pull request vs linked issue acceptance (read-only on GitHub).
Deliver markdown:
## Summary (title, state, scope)
## Issue acceptance (bullets vs delivery)
## Gaps (tests, docs, edge cases)
## Verdict (merge_ready | needs_work | needs_issue_update)
## Next step (`cli craft pr`, `cli craft issue`, or GitHub UI merge)"""


class CraftAI:
    """Thin orchestration over DeepSeek's three model roles."""

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    def complete(
        self,
        phase: CraftPhase,
        user: str,
        *,
        system: str | None = None,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> str:
        role = _ROLE[phase]
        sys_content = system or self._default_system(phase)
        return self._client.complete(
            [{"role": "system", "content": sys_content}, {"role": "user", "content": user}],
            role=role,
            temperature=temperature,
            json_mode=json_mode,
        )

    @staticmethod
    def _default_system(phase: CraftPhase) -> str:
        return {
            "issue_review": _ISSUE_REVIEW_SYSTEM,
            "issue_dedupe": _ISSUE_DEDUPE_SYSTEM,
            "issue_ship": _ISSUE_SHIP_SYSTEM,
            "issue_plan": _ISSUE_PLAN_SYSTEM,
            "issue_execute": _ISSUE_EXECUTE_SYSTEM,
            "pr_body": _PR_BODY_SYSTEM,
            "pr_review": _PR_REVIEW_SYSTEM,
            "code_guidance": (
                "You guide code changes for a GitHub issue. "
                "Output concrete file-level steps and patches where possible. "
                "Prefer minimal diffs matching repo conventions."
            ),
        }[phase]

    def review_issue(self, *, context: dict[str, Any], open_issues: list[dict[str, Any]]) -> str:
        payload = json.dumps(
            {"target": context, "open_issues": open_issues[:40]},
            indent=2,
            default=str,
        )[:24000]
        return self.complete("issue_review", payload)

    def dedupe(
        self,
        *,
        title: str,
        body: str,
        open_issues: list[dict[str, Any]],
        self_number: int | None = None,
    ) -> dict[str, Any]:
        user = json.dumps(
            {
                "candidate": {"title": title, "body_summary": body[:2000]},
                "self_number": self_number,
                "open_issues": [
                    {"number": i["number"], "title": i.get("title"), "labels": i.get("labels")}
                    for i in open_issues[:60]
                ],
            },
            indent=2,
        )
        raw = self.complete("issue_dedupe", user, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"verdict": "ambiguous", "reason": raw, "parse_error": True}

    def ship_spec(
        self,
        *,
        title: str,
        body: str,
        dedupe: dict[str, Any],
        repo: str,
        backlog: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        user = json.dumps(
            {
                "repo": repo,
                "intent": {"title": title, "body": body},
                "dedupe": dedupe,
                "backlog": backlog or {},
            },
            indent=2,
            default=str,
        )[:16000]
        raw = self.complete("issue_ship", user, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "title": title,
                "body": body,
                "labels": [],
                "action": "create",
                "parse_error": raw,
            }

    def plan_issue(self, *, context: dict[str, Any], runtime: str) -> str:
        user = (
            f"Runtime profile: {runtime}\n\n"
            f"Issue context:\n{json.dumps(context, indent=2, default=str)[:12000]}"
        )
        return self.complete("issue_plan", user)

    def execute_issue(self, *, context: dict[str, Any], plan_text: str) -> str:
        user = json.dumps(
            {"issue": context, "plan": plan_text[:8000]},
            indent=2,
            default=str,
        )[:16000]
        return self.complete("issue_execute", user)

    def pr_body(self, *, issue_context: dict[str, Any], diff_stat: str = "") -> str:
        user = json.dumps(
            {"issue": issue_context, "diff_stat": diff_stat[:4000]},
            indent=2,
            default=str,
        )[:12000]
        return self.complete("pr_body", user)

    def review_pr(
        self,
        *,
        pr_view: dict[str, Any],
        diff: str,
        linked_issues: list[dict[str, Any]],
    ) -> str:
        user = json.dumps(
            {
                "pr": pr_view,
                "diff_excerpt": diff[:12000],
                "linked_issues": linked_issues,
            },
            indent=2,
            default=str,
        )[:20000]
        return self.complete("pr_review", user)

    def code_guidance(self, *, context: dict[str, Any], title: str) -> str:
        user = (
            f"Implement: {title}\n\n"
            f"Context:\n{json.dumps(context, indent=2, default=str)[:10000]}"
        )
        return self.complete("code_guidance", user, temperature=0.2)
