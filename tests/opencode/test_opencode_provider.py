"""OpenCode provider — CLI wiring and output parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.providers.opencode import (
    OpenCodeProvider,
    model_for_role,
    parse_opencode_stdout,
    resolve_opencode_config,
)

from src.utils.paths import bundled_path

from src.utils.paths import bundled_path

ROOT = Path(__file__).resolve().parents[2]


def test_model_for_role_reads_config() -> None:
    assert model_for_role("reason") == "deepseek/deepseek-reasoner"
    assert model_for_role("chat") == "deepseek/deepseek-chat"


def test_resolve_opencode_config_uses_config_dir() -> None:
    path = resolve_opencode_config()
    assert path is not None
    assert path.is_file()
    assert path == bundled_path("opencode", "opencode.json")


def test_parse_opencode_stdout_plain_text() -> None:
    assert parse_opencode_stdout("hello\n") == "hello"


def test_parse_opencode_stdout_ndjson() -> None:
    lines = [
        json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
        json.dumps({"type": "text", "part": {"type": "text", "text": "pong"}}),
    ]
    assert parse_opencode_stdout("\n".join(lines)) == "pong"


@patch("src.providers.opencode.subprocess.run")
@patch("src.providers.opencode.shutil.which", return_value="/usr/bin/opencode")
def test_run_opencode_cli_uses_documented_flags(mock_which: MagicMock, mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    out = OpenCodeProvider(workspace_dir=ROOT).run_prompt("ping", tier="plan", mode="shot")

    assert out == "ok"
    assert mock_run.call_count >= 1
    argv = mock_run.call_args.args[0]
    assert argv[0] == "/usr/bin/opencode"
    assert argv[1:6] == ["run", "--auto", "--pure", "-m", "deepseek/deepseek-reasoner"]
    assert "--dir" in argv
    assert argv[-1] == "ping"
    env = mock_run.call_args.kwargs["env"]
    assert "OPENCODE_CONFIG" in env


@patch("src.providers.opencode.subprocess.run")
@patch("src.providers.opencode.shutil.which", return_value="/usr/bin/opencode")
def test_run_opencode_cli_honors_attach_env(mock_which: MagicMock, mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="via-attach", stderr="")

    with patch.dict("os.environ", {"OPENCODE_ATTACH": "http://127.0.0.1:4096"}, clear=False):
        out = OpenCodeProvider(workspace_dir=ROOT).run_prompt("ping", tier="code", mode="chat")

    assert out == "via-attach"
    argv = mock_run.call_args.args[0]
    idx = argv.index("--attach")
    assert argv[idx + 1] == "http://127.0.0.1:4096"


@patch("src.providers.opencode.shutil.which", return_value=None)
def test_run_prompt_falls_back_to_stub_without_cli_or_key(mock_which: MagicMock) -> None:
    with patch.dict("os.environ", {}, clear=True):
        out = OpenCodeProvider().run_prompt("hello", tier="summarize")
    payload = json.loads(out)
    assert payload["stub"] is True
