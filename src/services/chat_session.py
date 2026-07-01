"""Repo-agnostic chat sessions — stored outside any git repository."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.providers.deepseek import DeepSeekClient


def chat_root() -> Path:
    import os

    base = os.environ.get("CLI_CHAT_DIR")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".config" / "cli" / "chat"


@dataclass
class ChatMessage:
    role: str
    content: str
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content, "at": self.at}


class ChatSession:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.dir = chat_root() / "sessions" / session_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._messages_path = self.dir / "messages.jsonl"
        self._summary_path = self.dir / "summary.md"
        self._meta_path = self.dir / "meta.json"

    @classmethod
    def create(cls, session_id: str | None = None) -> ChatSession:
        sid = session_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        session = cls(sid)
        if not session._meta_path.exists():
            session._meta_path.write_text(
                json.dumps({"id": sid, "created": datetime.now(timezone.utc).isoformat()}, indent=2),
                encoding="utf-8",
            )
        return session

    @classmethod
    def load(cls, session_id: str) -> ChatSession:
        session = cls(session_id)
        if not session._messages_path.exists() and not session._meta_path.exists():
            raise FileNotFoundError(f"Chat session not found: {session_id}")
        return session

    @classmethod
    def list_sessions(cls) -> list[str]:
        root = chat_root() / "sessions"
        if not root.is_dir():
            return []
        return sorted(p.name for p in root.iterdir() if p.is_dir())

    def append(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role=role, content=content)
        with self._messages_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg.to_dict()) + "\n")
        return msg

    def messages(self) -> list[dict[str, str]]:
        if not self._messages_path.is_file():
            return []
        out: list[dict[str, str]] = []
        for line in self._messages_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def transcript_text(self, *, max_messages: int | None = None) -> str:
        msgs = self.messages()
        if max_messages:
            msgs = msgs[-max_messages:]
        parts = []
        for m in msgs:
            parts.append(f"{m['role'].upper()}: {m['content']}")
        return "\n\n".join(parts)

    def summary(self) -> str:
        if self._summary_path.is_file():
            return self._summary_path.read_text(encoding="utf-8")
        return ""

    def set_summary(self, text: str) -> None:
        self._summary_path.write_text(text.strip() + "\n", encoding="utf-8")

    def artifact_path(self, name: str) -> Path:
        return self.dir / name

    def refresh_summary(self, client: DeepSeekClient | None = None) -> str:
        client = client or DeepSeekClient()
        transcript = self.transcript_text()
        if not transcript.strip():
            return ""
        prior = self.summary()
        prompt = (
            "You maintain a rolling plan summary for a multi-repo software discussion.\n"
            "Update the summary: goals, decisions, open questions, cross-repo impacts.\n"
            "Be concise (markdown bullets). Do not invent facts.\n\n"
            f"PRIOR SUMMARY:\n{prior or '(none)'}\n\n"
            f"FULL TRANSCRIPT:\n{transcript}\n"
        )
        summary = client.complete(
            [
                {"role": "system", "content": "You summarize planning chats for later GitHub issue filing."},
                {"role": "user", "content": prompt},
            ],
            role="chat",
            temperature=0.3,
        )
        self.set_summary(summary)
        return summary

    def reply(self, user_text: str, client: DeepSeekClient | None = None) -> str:
        client = client or DeepSeekClient()
        self.append("user", user_text)
        summary = self.summary()
        recent = self.transcript_text(max_messages=12)
        system = (
            "You are a planning partner for gardusig open-source repos. "
            "The chat is NOT tied to a single repository. "
            "Help clarify ideas; note cross-repo impacts when relevant. "
            "Do not run git or file issues unless asked."
        )
        user = (
            f"ROLLING SUMMARY:\n{summary or '(empty)'}\n\n"
            f"RECENT MESSAGES:\n{recent}\n\n"
            f"USER:\n{user_text}"
        )
        assistant = client.complete(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            role="chat",
        )
        self.append("assistant", assistant)
        self.refresh_summary(client)
        return assistant

    def export_bundle(self) -> dict[str, Any]:
        bundle: dict[str, Any] = {
            "session_id": self.session_id,
            "summary": self.summary(),
            "transcript": self.transcript_text(),
            "messages": self.messages(),
        }
        for name in ("distill-r1.json", "categorize.json"):
            path = self.artifact_path(name)
            if path.is_file():
                bundle[name.replace(".json", "")] = json.loads(path.read_text(encoding="utf-8"))
        return bundle
