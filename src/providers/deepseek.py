"""DeepSeek Chat Completions API — direct httpx client."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import httpx
import yaml

from src.utils.paths import bundled_path

Role = Literal["chat", "reason", "categorize"]

_CONFIG_PATH = bundled_path("deepseek", "models.yaml")


class DeepSeekError(RuntimeError):
    pass


def _load_config() -> dict[str, Any]:
    if not _CONFIG_PATH.is_file():
        return {"api_base": "https://api.deepseek.com", "roles": {}}
    return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}


def model_for_role(role: Role) -> str:
    cfg = _load_config()
    roles = cfg.get("roles") or {}
    env_key = f"DEEPSEEK_MODEL_{role.upper()}"
    if os.environ.get(env_key):
        return os.environ[env_key]
    entry = roles.get(role) or {}
    return str(entry.get("model") or "deepseek-chat")


def api_base() -> str:
    return os.environ.get("DEEPSEEK_API_BASE") or str(_load_config().get("api_base") or "https://api.deepseek.com")


def api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY")


class DeepSeekClient:
    """Minimal chat completions client."""

    def __init__(self, *, timeout: float = 120.0) -> None:
        self.timeout = timeout

    def available(self) -> bool:
        return bool(api_key())

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        role: Role = "chat",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        key = api_key()
        if not key:
            return self._stub(messages, role=role)

        model = model_for_role(role)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{api_base().rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise DeepSeekError(f"DeepSeek API {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise DeepSeekError(f"Unexpected API response: {data!r}") from exc

    @staticmethod
    def _stub(messages: list[dict[str, str]], *, role: Role) -> str:
        last = messages[-1]["content"][:200] if messages else ""
        if role == "categorize":
            return json.dumps(
                {
                    "stub": True,
                    "repos": [],
                    "note": "Set DEEPSEEK_API_KEY for live categorization.",
                    "prompt_preview": last,
                },
                indent=2,
            )
        return json.dumps(
            {
                "stub": True,
                "role": role,
                "note": "Set DEEPSEEK_API_KEY for live chat.",
                "echo": last,
            },
            indent=2,
        )
