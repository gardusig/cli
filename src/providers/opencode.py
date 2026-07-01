"""OpenCode provider — DeepSeek 3-model roles; optional opencode CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Literal

import shutil

from src.providers.deepseek import DeepSeekClient, Role

ModelTier = Literal["plan", "summarize", "code", "categorize"]

# plan/code → reason (R1); summarize → chat; categorize → categorize (R4-class)
_TIER_ROLE: dict[ModelTier, Role] = {
    "plan": "reason",
    "code": "reason",
    "summarize": "chat",
    "categorize": "categorize",
}


class OpenCodeProvider:
    """Delegates to DeepSeek API; invokes `opencode` CLI when on PATH."""

    def __init__(self, *, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.home() / ".config" / "cli" / "opencode"
        self._opencode_bin = shutil.which("opencode")
        self._deepseek = DeepSeekClient()

    @property
    def available(self) -> bool:
        return self._opencode_bin is not None or self._deepseek.available()

    def run_prompt(
        self,
        prompt: str,
        *,
        tier: ModelTier = "summarize",
        mode: Literal["shot", "chat"] = "shot",
    ) -> str:
        if self._opencode_bin and tier == "code" and mode == "chat":
            cli_out = self._run_opencode_cli(prompt, tier=tier)
            if cli_out:
                return cli_out

        if self._deepseek.available():
            role = _TIER_ROLE.get(tier, "chat")
            return self._deepseek.complete(
                [
                    {
                        "role": "system",
                        "content": (
                            f"OpenCode tier={tier} mode={mode}. "
                            f"Model role={role}. Follow repo conventions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                role=role,
            )
        return self._stub_response(prompt, tier=tier, mode=mode)

    def _run_opencode_cli(self, prompt: str, *, tier: ModelTier) -> str | None:
        """Best-effort opencode subprocess; returns None on failure."""
        if not self._opencode_bin:
            return None
        model = _TIER_ROLE.get(tier, "reason")
        for args in (
            ["run", "--model", model, prompt],
            ["chat", "--model", model, "-p", prompt],
            ["-p", prompt],
        ):
            try:
                proc = subprocess.run(
                    [self._opencode_bin, *args],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        return None

    @staticmethod
    def _stub_response(prompt: str, *, tier: ModelTier, mode: str) -> str:
        preview = prompt.strip().replace("\n", " ")[:120]
        return json.dumps(
            {
                "tier": tier,
                "mode": mode,
                "role": _TIER_ROLE.get(tier, "chat"),
                "stub": True,
                "note": "Set DEEPSEEK_API_KEY for live output.",
                "prompt_preview": preview,
            },
            indent=2,
        )
