"""Registry of public API-backed CLI commands for mocked integration checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.cli import app
from src.integration.public_endpoints import REFUSE_NEEDLE

ApiName = Literal["notion", "drive", "chrome"]
CheckKind = Literal["ok", "fail"]

_OPTION_TAKES_VALUE = frozenset(
    {
        "--format",
        "--file",
        "--manifest",
        "--title",
        "--body",
        "--base",
        "--head",
        "--state",
        "--limit",
        "--label",
        "--query",
        "--json-fields",
        "--color",
        "--description",
        "--comment",
        "--merge-method",
        "--body-file",
        "--id",
        "--project",
        "--owner",
        "--url",
        "--issue",
        "--pr",
        "--lane",
        "--field",
        "--value",
        "--kind",
        "--readme",
        "--visibility",
        "--transport",
        "--readme",
    }
)


def command_tokens(args: tuple[str, ...]) -> tuple[str, ...]:
    """Drop flags and flag values; keep command path tokens only."""
    tokens: list[str] = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("-"):
            if arg in _OPTION_TAKES_VALUE:
                skip_next = True
            continue
        tokens.append(arg)
    return tuple(tokens)


def command_path(args: tuple[str, ...]) -> tuple[str, ...]:
    """Normalized command path (e.g. notion, ingest)."""
    return command_tokens(args)


def _args_include_path(args: tuple[str, ...], path: tuple[str, ...]) -> bool:
    tokens = command_tokens(args)
    return len(tokens) >= len(path) and tokens[: len(path)] == path


def _without_yes(args: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(arg for arg in args if arg != "--yes")


@dataclass(frozen=True)
class CliApiCheck:
    """One cli CLI invocation against a mocked remote API."""

    label: str
    api: ApiName
    args: tuple[str, ...]
    needle: str | None = None
    kind: CheckKind = "ok"
    accept_exit_codes: tuple[int, ...] = (0,)
    extra_env: dict[str, str] | None = None
    failure: str | None = None  # gh_auth | refuse_gate | missing_token | ...


def _visible_commands(typer_app, prefix: tuple[str, ...]) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    for cmd in typer_app.registered_commands:
        if cmd.hidden:
            continue
        name = cmd.name or ""
        if name:
            paths.add((*prefix, name))
    for group in typer_app.registered_groups:
        if group.hidden:
            continue
        gname = group.name or ""
        if gname:
            paths |= _visible_commands(group.typer_instance, (*prefix, gname))
    return paths


def registered_api_command_paths(api: ApiName) -> set[tuple[str, ...]]:
    """Visible Typer command paths for notion, drive, or chrome."""
    for group in app.registered_groups:
        if group.name == api:
            return _visible_commands(group.typer_instance, (api,))
    return set()

def _notion_success_checks() -> list[CliApiCheck]:
    return [
        CliApiCheck("notion ingest", "notion", ("notion", "ingest"), "ingested"),
        CliApiCheck(
            "notion deploy",
            "notion",
            ("notion", "deploy", "--yes", "--no-cleanup"),
            "deployed",
        ),
        CliApiCheck(
            "notion sync",
            "notion",
            ("notion", "sync", "--yes", "--no-cleanup"),
            "Phase 2",
        ),
        CliApiCheck("notion cleanup", "notion", ("notion", "cleanup", "--yes"), "archived"),
        CliApiCheck("notion pairs build", "notion", ("notion", "pairs", "build"), "built"),
        CliApiCheck("notion pairs status", "notion", ("notion", "pairs", "status"), "deploy:"),
    ]


def _notion_failure_checks() -> list[CliApiCheck]:
    return [
        CliApiCheck(
            "notion ingest missing token",
            "notion",
            ("notion", "ingest"),
            kind="fail",
            needle="NOTION_TOKEN",
            accept_exit_codes=(1,),
            failure="missing_token",
        ),
        CliApiCheck(
            "notion deploy missing manifest",
            "notion",
            ("notion", "deploy", "--yes", "--no-cleanup"),
            kind="fail",
            needle="pairs build",
            accept_exit_codes=(1,),
            failure="missing_manifest",
        ),
        CliApiCheck(
            "notion sync missing token",
            "notion",
            ("notion", "sync", "--yes", "--no-cleanup"),
            kind="fail",
            needle="NOTION_TOKEN",
            accept_exit_codes=(1,),
            failure="missing_token",
        ),
        CliApiCheck(
            "notion cleanup refuse",
            "notion",
            ("notion", "cleanup"),
            kind="fail",
            needle=REFUSE_NEEDLE,
            accept_exit_codes=(1,),
            failure="refuse_gate",
        ),
        CliApiCheck(
            "notion pairs build orphans",
            "notion",
            ("notion", "pairs", "build"),
            kind="fail",
            needle="header without body",
            accept_exit_codes=(1,),
            failure="notion_orphans",
        ),
        CliApiCheck(
            "notion pairs status missing manifest",
            "notion",
            ("notion", "pairs", "status"),
            kind="fail",
            needle="pairs build",
            accept_exit_codes=(1,),
            failure="missing_manifest",
        ),
    ]


def _drive_success_checks(repo_path: str) -> list[CliApiCheck]:
    return [
        CliApiCheck("drive status", "drive", ("drive", "status"), "Repository:"),
        CliApiCheck("drive ingest", "drive", ("drive", "ingest"), "Done."),
        CliApiCheck("drive list", "drive", ("drive", "list", repo_path), "Local zips"),
        CliApiCheck(
            "drive delete",
            "drive",
            ("drive", "delete", repo_path, "v0.0.0", "--yes"),
            "deleted",
        ),
        CliApiCheck("drive upload", "drive", ("drive", "upload", "google"), "Uploading"),
        CliApiCheck("drive download", "drive", ("drive", "download", "google"), "Downloading"),
        CliApiCheck("drive deploy", "drive", ("drive", "deploy"), "Done."),
        CliApiCheck("drive sync", "drive", ("drive", "sync"), "Phase 2"),
        CliApiCheck(
            "drive sync dry-run",
            "drive",
            ("drive", "sync", "--dry-run", "--format", "json"),
            '"dry_run": true',
        ),
        CliApiCheck(
            "drive sync status",
            "drive",
            ("drive", "sync", "--status", "--format", "json"),
            '"status": true',
        ),
    ]


def _drive_failure_checks(repo_path: str) -> list[CliApiCheck]:
    return [
        CliApiCheck(
            "drive delete refuse",
            "drive",
            ("drive", "delete", repo_path, "v0.0.0"),
            kind="fail",
            needle=REFUSE_NEEDLE,
            accept_exit_codes=(1,),
            failure="refuse_gate",
        ),
        CliApiCheck(
            "drive upload missing tags dir",
            "drive",
            ("drive", "upload", "google"),
            kind="fail",
            needle="git-tags",
            accept_exit_codes=(1,),
            failure="missing_tags_dir",
        ),
        CliApiCheck(
            "drive sync missing tags dir",
            "drive",
            ("drive", "sync"),
            kind="fail",
            needle="git-tags",
            accept_exit_codes=(1,),
            failure="missing_tags_dir",
        ),
        CliApiCheck(
            "drive deploy missing tags dir",
            "drive",
            ("drive", "deploy"),
            kind="fail",
            needle="git-tags",
            accept_exit_codes=(1,),
            failure="missing_tags_dir",
        ),
        CliApiCheck(
            "drive download missing tags dir",
            "drive",
            ("drive", "download", "google"),
            kind="fail",
            needle="git-tags",
            accept_exit_codes=(1,),
            failure="missing_tags_dir",
        ),
        CliApiCheck(
            "drive ingest fail",
            "drive",
            ("drive", "ingest"),
            kind="fail",
            needle="ingest failed",
            accept_exit_codes=(1,),
            failure="drive_ingest_error",
        ),
        CliApiCheck(
            "drive list bad repo",
            "drive",
            ("drive", "list", "/no/such/repo"),
            kind="fail",
            needle="Not a directory",
            accept_exit_codes=(1,),
            failure="drive_bad_repo",
        ),
        CliApiCheck(
            "drive status error",
            "drive",
            ("drive", "status"),
            kind="fail",
            needle="status failed",
            accept_exit_codes=(1,),
            failure="drive_status_error",
        ),
    ]


def _chrome_success_checks() -> list[CliApiCheck]:
    return [
        CliApiCheck("chrome bookmarks ingest", "chrome", ("chrome", "bookmarks", "ingest"), "ingested"),
        CliApiCheck(
            "chrome bookmarks deploy",
            "chrome",
            ("chrome", "bookmarks", "deploy"),
            "ready",
        ),
        CliApiCheck(
            "chrome bookmarks merge",
            "chrome",
            ("chrome", "bookmarks", "merge"),
            "Added",
        ),
        CliApiCheck(
            "chrome bookmarks snapshot",
            "chrome",
            ("chrome", "bookmarks", "snapshot"),
            "snapshot",
        ),
        CliApiCheck(
            "chrome photos list",
            "chrome",
            ("chrome", "photos", "list", "--format", "json"),
            '"albums"',
        ),
        CliApiCheck(
            "chrome photos status",
            "chrome",
            ("chrome", "photos", "status"),
            "photos_dir",
        ),
        CliApiCheck(
            "chrome photos ingest",
            "chrome",
            ("chrome", "photos", "ingest", "--yes"),
            "Ingested",
        ),
    ]


def _chrome_failure_checks() -> list[CliApiCheck]:
    return [
        CliApiCheck(
            "chrome bookmarks ingest timeout",
            "chrome",
            ("chrome", "bookmarks", "ingest"),
            kind="fail",
            needle=None,
            accept_exit_codes=(1,),
            failure="chrome_no_fixture",
        ),
        CliApiCheck(
            "chrome bookmarks deploy missing",
            "chrome",
            ("chrome", "bookmarks", "deploy"),
            kind="fail",
            needle="Backup not found",
            accept_exit_codes=(1,),
            failure="missing_bookmarks",
        ),
        CliApiCheck(
            "chrome photos ingest no takeout",
            "chrome",
            ("chrome", "photos", "ingest", "--yes"),
            kind="fail",
            needle=None,
            accept_exit_codes=(1,),
            failure="chrome_photos_no_takeout",
        ),
        CliApiCheck(
            "chrome photos list missing dir",
            "chrome",
            ("chrome", "photos", "list"),
            kind="fail",
            needle="photos_dir",
            accept_exit_codes=(1,),
            failure="chrome_photos_no_dir",
        ),
        CliApiCheck(
            "chrome photos status missing dir",
            "chrome",
            ("chrome", "photos", "status"),
            kind="fail",
            needle="photos_dir",
            accept_exit_codes=(1,),
            failure="chrome_photos_no_dir",
        ),
        CliApiCheck(
            "chrome bookmarks merge no source",
            "chrome",
            ("chrome", "bookmarks", "merge"),
            kind="fail",
            needle="No HTML export",
            accept_exit_codes=(1,),
            failure="chrome_merge_no_source",
        ),
        CliApiCheck(
            "chrome bookmarks snapshot missing dir",
            "chrome",
            ("chrome", "bookmarks", "snapshot"),
            kind="fail",
            needle="snapshots_dir",
            accept_exit_codes=(1,),
            failure="chrome_no_snapshots_dir",
        ),
    ]


def cli_api_success_checks(*, drive_repo: str) -> list[CliApiCheck]:
    return [
        *_notion_success_checks(),
        *_drive_success_checks(drive_repo),
        *_chrome_success_checks(),
    ]


def cli_api_failure_checks(*, drive_repo: str) -> list[CliApiCheck]:
    return [
        *_notion_failure_checks(),
        *_drive_failure_checks(drive_repo),
        *_chrome_failure_checks(),
    ]


def cli_api_checks(*, drive_repo: str) -> list[CliApiCheck]:
    return [
        *cli_api_success_checks(drive_repo=drive_repo),
        *cli_api_failure_checks(drive_repo=drive_repo),
    ]


def checks_for_path(
    checks: list[CliApiCheck],
    *,
    api: ApiName,
    path: tuple[str, ...],
) -> list[CliApiCheck]:
    return [
        check
        for check in checks
        if check.api == api and _args_include_path(check.args, path)
    ]


def assert_cli_api_registry_covers_commands(
    checks: list[CliApiCheck],
    *,
    apis: tuple[ApiName, ...] = ("notion", "drive", "chrome"),
) -> None:
    """Every visible API subcommand must have a mocked CLI integration check."""
    for api in apis:
        expected = registered_api_command_paths(api)
        missing = [
            path
            for path in sorted(expected)
            if not checks_for_path(checks, api=api, path=path)
        ]
        if missing:
            raise AssertionError(
                f"{api} CLI API checks missing command paths: {missing} "
                f"(registered: {sorted(expected)})"
            )


def assert_every_api_command_has_ok_and_fail_check(
    checks: list[CliApiCheck],
    *,
    apis: tuple[ApiName, ...] = ("notion", "drive", "chrome"),
) -> None:
    """Each API command path needs one success and one failure integration check."""
    local_ok_only: dict[ApiName, set[tuple[str, ...]]] = {}
    local_fail_only: dict[ApiName, set[tuple[str, ...]]] = {
        "chrome": set(),
    }
    assert_cli_api_registry_covers_commands(checks, apis=apis)
    for api in apis:
        for path in sorted(registered_api_command_paths(api)):
            rows = checks_for_path(checks, api=api, path=path)
            kinds = {check.kind for check in rows}
            if path in local_fail_only.get(api, set()):
                if "fail" not in kinds:
                    raise AssertionError(
                        f"{api} {' '.join(path)} missing fail check "
                        f"(have kinds={sorted(kinds)}, labels={[c.label for c in rows]})"
                    )
                continue
            if path in local_ok_only.get(api, set()):
                if "ok" not in kinds:
                    raise AssertionError(
                        f"{api} {' '.join(path)} missing ok check "
                        f"(have kinds={sorted(kinds)}, labels={[c.label for c in rows]})"
                    )
                continue
            if "ok" not in kinds or "fail" not in kinds:
                raise AssertionError(
                    f"{api} {' '.join(path)} missing ok/fail checks "
                    f"(have kinds={sorted(kinds)}, labels={[c.label for c in rows]})"
                )


def validate_cli_api_check(check: CliApiCheck, *, exit_code: int, output: str) -> str | None:
    """Return an error message when the invocation does not match the check contract."""
    if check.kind == "ok":
        if exit_code not in check.accept_exit_codes:
            return f"expected exit {check.accept_exit_codes}, got {exit_code}\n{output}"
    elif exit_code not in check.accept_exit_codes:
        return f"expected exit {check.accept_exit_codes}, got {exit_code}\n{output}"
    elif exit_code == 0 and check.kind == "fail" and 0 not in check.accept_exit_codes:
        return f"expected failure, got exit 0\n{output}"
    if check.needle and check.needle not in output:
        return f"missing needle {check.needle!r}\n{output}"
    return None
