from __future__ import annotations

from pathlib import Path

from src.services.toolkit.catalog import CommandSpec, command_spec
from src.services.toolkit.detect import confirm_markers, repo_languages
from src.services.toolkit.handlers import run_handler
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
    env = _handler_env(spec, workspace, extra_env=extra_env)
    return run_handler(spec, workspace, env)


def _handler_env(spec: CommandSpec, workspace: Path, *, extra_env: dict[str, str] | None) -> dict[str, str]:
    env = {
        "WORKSPACE": str(workspace),
        "CLI_GROUP": spec.group,
        "CLI_SUBJECT": spec.subject,
        "CLI_SUITE": spec.suite or "",
    }
    if spec.group == "lint" and spec.subject == "repo":
        env["CLI_LINT_LANGUAGES"] = " ".join(repo_languages(workspace))
    if extra_env:
        env.update({key: value for key, value in extra_env.items() if value != ""})
    return env

