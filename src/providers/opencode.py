"""OpenCode subprocess provider — DeepSeek tiers for craft/review."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

ModelTier = Literal["plan", "summarize", "code"]

_TIER_MODELS: dict[ModelTier, str] = {
    "plan": "deepseek/deepseek-chat",
    "summarize": "deepseek/deepseek-chat",
    "code": "deepseek/deepseek-chat",
}


class OpenCodeProvider:
    """Thin wrapper around `opencode` CLI when installed."""

    def __init__(self, *, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.home() / ".config" / "cli" / "opencode"
        self._available = shutil.which("opencode") is not None

    @property
    def available(self) -> bool:
        return self._available

    def run_prompt(
        self,
        prompt: str,
        *,
        tier: ModelTier = "summarize",
        mode: Literal["shot", "chat"] = "shot",
    ) -> str:
        if not self._available:
            return self._stub_response(prompt, tier=tier, mode=mode)
        model = _TIER_MODELS[tier]
        args = ["opencode", "run", "--model", model, "--message", prompt]
        if mode == "chat":
            args.insert(2, "--continue")
        env = os.environ.copy()
        if self.config_dir.exists():
            env["OPENCODE_CONFIG_DIR"] = str(self.config_dir)
        result = subprocess.run(args, capture_output=True, text=True, check=False, env=env)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "opencode failed")
        return result.stdout.strip()

    @staticmethod
    def _stub_response(prompt: str, *, tier: ModelTier, mode: str) -> str:
        preview = prompt.strip().replace("\n", " ")[:120]
        return json.dumps(
            {
                "tier": tier,
                "mode": mode,
                "stub": True,
                "note": "Install opencode and set DEEPSEEK_API_KEY for live output.",
                "prompt_preview": preview,
            },
            indent=2,
        )
