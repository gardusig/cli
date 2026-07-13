"""OpenCode provider — DeepSeek roles; optional `opencode` CLI integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal

import yaml

from src.providers.deepseek import DeepSeekClient, Role
from src.utils.config import default_config_dir

ModelTier = Literal["plan", "summarize", "code", "categorize"]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MODELS_PATH = _REPO_ROOT / "config" / "opencode" / "models.yaml"
_BUNDLED_CONFIG = _REPO_ROOT / "config" / "opencode" / "opencode.json"

# plan/code → reason (R1); summarize → chat; categorize → categorize (R4-class)
_TIER_ROLE: dict[ModelTier, Role] = {
    "plan": "reason",
    "code": "reason",
    "summarize": "chat",
    "categorize": "categorize",
}


def _load_models_config() -> dict[str, Any]:
    if not _MODELS_PATH.is_file():
        return {"roles": {}, "default_model": "deepseek/deepseek-chat"}
    return yaml.safe_load(_MODELS_PATH.read_text(encoding="utf-8")) or {}


def model_for_role(role: Role) -> str:
    """Resolve OpenCode provider/model id for a DeepSeek role."""
    cfg = _load_models_config()
    env_key = f"OPENCODE_MODEL_{role.upper()}"
    if os.environ.get(env_key):
        return os.environ[env_key]
    roles = cfg.get("roles") or {}
    entry = roles.get(role) or {}
    return str(entry.get("model") or cfg.get("default_model") or "deepseek/deepseek-chat")


def resolve_opencode_config(*, config_dir: Path | None = None) -> Path | None:
    """Pick the OpenCode config file passed to the CLI via OPENCODE_CONFIG."""
    override = os.environ.get("OPENCODE_CONFIG", "").strip()
    if override:
        path = Path(override).expanduser()
        return path if path.is_file() else None

    base = (config_dir or default_config_dir() / "opencode").expanduser()
    for candidate in (base / "opencode.json", _BUNDLED_CONFIG):
        if candidate.is_file():
            return candidate
    return None


def parse_opencode_stdout(stdout: str) -> str | None:
    """Parse `opencode run` stdout (default text or ndjson events)."""
    text = stdout.strip()
    if not text:
        return None
    if not text.startswith("{"):
        return text

    chunks: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "text":
            continue
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text":
            chunks.append(str(part.get("text") or ""))
    joined = "".join(chunks).strip()
    return joined or None


class OpenCodeProvider:
    """Delegates to the `opencode` CLI when available, else DeepSeek HTTP API."""

    def __init__(self, *, config_dir: Path | None = None, workspace_dir: Path | None = None) -> None:
        self.config_dir = config_dir or default_config_dir() / "opencode"
        self.workspace_dir = (workspace_dir or Path.cwd()).resolve()
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
        if self._opencode_bin:
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

    def _subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        cfg = resolve_opencode_config(config_dir=self.config_dir)
        if cfg is not None and "OPENCODE_CONFIG" not in env:
            env["OPENCODE_CONFIG"] = str(cfg.resolve())
        return env

    def _run_timeout(self) -> float:
        raw = os.environ.get("OPENCODE_TIMEOUT", "300").strip()
        try:
            return max(30.0, float(raw))
        except ValueError:
            return 300.0

    def _attach_url(self) -> str | None:
        for key in ("OPENCODE_ATTACH", "OPENCODE_ATTACH_URL", "OPENCODE_SERVE_URL"):
            value = os.environ.get(key, "").strip()
            if value:
                return value
        return None

    def _run_opencode_cli(self, prompt: str, *, tier: ModelTier) -> str | None:
        """Best-effort `opencode run`; returns None on failure."""
        if not self._opencode_bin:
            return None

        role = _TIER_ROLE.get(tier, "chat")
        model = model_for_role(role)
        base_args = [
            "run",
            "--auto",
            "--pure",
            "-m",
            model,
            "--dir",
            str(self.workspace_dir),
        ]
        attach = self._attach_url()
        if attach:
            base_args.extend(["--attach", attach])

        env = self._subprocess_env()
        timeout = self._run_timeout()

        for fmt in ("default", "json"):
            args = [*base_args]
            if fmt == "json":
                args.extend(["--format", "json"])
            args.append(prompt)
            try:
                proc = subprocess.run(
                    [self._opencode_bin, *args],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                    env=env,
                    cwd=self.workspace_dir,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if proc.returncode != 0:
                continue
            parsed = parse_opencode_stdout(proc.stdout)
            if parsed:
                return parsed
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
                "note": "Install `opencode` on PATH and/or set DEEPSEEK_API_KEY for live output.",
                "prompt_preview": preview,
            },
            indent=2,
        )
