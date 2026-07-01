"""OpenCode subprocess provider — delegates to DeepSeek when opencode absent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import shutil

from src.providers.deepseek import DeepSeekClient

ModelTier = Literal["plan", "summarize", "code"]

_TIER_ROLE = {
    "plan": "categorize",
    "summarize": "chat",
    "code": "categorize",
}


class OpenCodeProvider:
    """Thin wrapper — prefers DeepSeek API; opencode CLI optional."""

    def __init__(self, *, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.home() / ".config" / "cli" / "opencode"
        self._opencode = shutil.which("opencode") is not None
        self._deepseek = DeepSeekClient()

    @property
    def available(self) -> bool:
        return self._opencode or self._deepseek.available()

    def run_prompt(
        self,
        prompt: str,
        *,
        tier: ModelTier = "summarize",
        mode: Literal["shot", "chat"] = "shot",
    ) -> str:
        if self._deepseek.available():
            role = _TIER_ROLE.get(tier, "chat")
            return self._deepseek.complete(
                [
                    {"role": "system", "content": f"Tier: {tier}, mode: {mode}"},
                    {"role": "user", "content": prompt},
                ],
                role=role,  # type: ignore[arg-type]
            )
        return self._stub_response(prompt, tier=tier, mode=mode)

    @staticmethod
    def _stub_response(prompt: str, *, tier: ModelTier, mode: str) -> str:
        preview = prompt.strip().replace("\n", " ")[:120]
        return json.dumps(
            {
                "tier": tier,
                "mode": mode,
                "stub": True,
                "note": "Set DEEPSEEK_API_KEY for live output.",
                "prompt_preview": preview,
            },
            indent=2,
        )
