from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src.services.toolkit.catalog import CommandSpec, command_spec
from src.services.toolkit.detect import confirm_markers, repo_languages
from src.services.toolkit.prereqs import check_prereqs


def run_cli_command(
    group: str,
    subject: str,
    workspace: Path,
    *,
    suite: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> int:
    spec = command_spec(group, subject, suite)
    workspace = workspace.expanduser().resolve()
    if spec.markers:
        confirm_markers(workspace, spec.markers)
    if spec.requires_bins or spec.requires_any_bins:
        check_prereqs(spec.requires_bins, spec.requires_any_bins)
    env = _script_env(spec, workspace, extra_env=extra_env)
    script = _resolve_script(spec.script)
    return subprocess.run(["bash", str(script)], env=env, check=False).returncode


def _script_env(spec: CommandSpec, workspace: Path, *, extra_env: dict[str, str] | None) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "CLI_BIN": env.get("CLI_BIN", f"{sys.executable} -m src"),
            "WORKSPACE": str(workspace),
            "CLI_GROUP": spec.group,
            "CLI_SUBJECT": spec.subject,
            "CLI_SUITE": spec.suite or "",
            "CLI_TOOLKIT_ROOT": str(_scripts_root()),
        }
    )
    if spec.group == "lint" and spec.subject == "repo":
        env["CLI_LINT_LANGUAGES"] = " ".join(repo_languages(workspace))
    if extra_env:
        env.update({key: value for key, value in extra_env.items() if value != ""})
    return env


def _resolve_script(relative_path: str) -> Path:
    root = _scripts_root()
    script = root / Path(relative_path).relative_to("scripts")
    if not script.is_file():
        raise FileNotFoundError(f"Missing script: {script}")
    return script


def _scripts_root() -> Path:
    source_root = Path(__file__).resolve().parents[2] / "scripts"
    if source_root.is_dir():
        return source_root
    installed_root = Path(sys.prefix) / "share" / "gardusig-cli" / "scripts"
    return installed_root

