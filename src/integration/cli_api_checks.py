"""Registry of public API-backed CLI commands for mocked integration checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.cli import app
from src.integration.public_endpoints import REFUSE_NEEDLE

ApiName = Literal["gh", "notion", "drive", "chrome"]
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
    """Normalized command path (e.g. gh, issue, list)."""
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
    """Visible Typer command paths for gh, notion, drive, or chrome."""
    for group in app.registered_groups:
        if group.name == api:
            return _visible_commands(group.typer_instance, (api,))
    return set()


def _gh_success_checks(workspace: Path) -> list[CliApiCheck]:
    fmt = ("--format", "json")
    manifest = workspace / "labels.manifest.yaml"
    batch = workspace / "issue-batch.yaml"
    plan = workspace / "resequence.yaml"
    return [
        CliApiCheck("gh issue list", "gh", ("gh", *fmt, "issue", "list"), "Integration issue"),
        CliApiCheck(
            "gh issue list api",
            "gh",
            ("gh", "--transport", "api", "--repo", "example/repo", *fmt, "issue", "list"),
            '"number"',
        ),
        CliApiCheck(
            "gh pr checks api",
            "gh",
            ("gh", "--transport", "api", "--repo", "example/repo", *fmt, "pr", "checks", "7"),
            "ci",
        ),
        CliApiCheck(
            "gh project view api",
            "gh",
            ("gh", "--transport", "api", "project", "view", "1", "--owner", "owner"),
            "graphql",
        ),
        CliApiCheck(
            "gh project item add api",
            "gh",
            (
                "gh",
                "--transport",
                "api",
                "--yes",
                "project",
                "item",
                "add",
                "--project",
                "1",
                "--owner",
                "owner",
                "--issue",
                "42",
            ),
            "ITEM_1",
        ),
        CliApiCheck(
            "gh transport refuse",
            "gh",
            ("gh", "--transport", "api", *fmt, "issue", "list"),
            kind="fail",
            needle="GitHub API transport needs",
            accept_exit_codes=(1,),
            failure="gh_transport",
        ),
        CliApiCheck("gh issue view", "gh", ("gh", *fmt, "issue", "view", "42"), "fixture body"),
        CliApiCheck(
            "gh issue context",
            "gh",
            ("gh", *fmt, "issue", "context", "2"),
            "epic:wf-test",
        ),
        CliApiCheck("gh issue search", "gh", ("gh", *fmt, "issue", "search", "is:open"), "["),
        CliApiCheck(
            "gh issue create",
            "gh",
            ("gh", *fmt, "issue", "create", "--title", "New", "--body", "b", "--yes"),
            "example/repo/issues/",
        ),
        CliApiCheck(
            "gh issue edit",
            "gh",
            ("gh", *fmt, "issue", "edit", "42", "--title", "Edited", "--yes"),
            "edit",
        ),
        CliApiCheck(
            "gh issue reopen",
            "gh",
            ("gh", *fmt, "issue", "reopen", "42", "--yes"),
            "open",
        ),
        CliApiCheck("gh issue status", "gh", ("gh", *fmt, "issue", "status"), "open_issues"),
        CliApiCheck(
            "gh issue close",
            "gh",
            ("gh", *fmt, "issue", "close", "42", "--yes"),
            "close",
        ),
        CliApiCheck(
            "gh issue comment",
            "gh",
            ("gh", *fmt, "issue", "comment", "42", "--body", "hi", "--yes"),
            "comment",
        ),
        CliApiCheck(
            "gh issue delete",
            "gh",
            ("gh", *fmt, "issue", "delete", "42", "--yes"),
            "delete",
        ),
        CliApiCheck(
            "gh issue batch",
            "gh",
            ("gh", *fmt, "issue", "batch", "--file", str(batch), "--yes"),
            "Batch create",
        ),
        CliApiCheck(
            "gh issues deploy",
            "gh",
            ("gh", *fmt, "issues", "deploy", "--yes"),
            "deploy",
        ),
        CliApiCheck("gh issues ingest", "gh", ("gh", *fmt, "issues", "ingest"), "ingest"),
        CliApiCheck(
            "gh issues prune",
            "gh",
            ("gh", *fmt, "issues", "prune", "--yes"),
            "prune",
        ),
        CliApiCheck("gh label list", "gh", ("gh", *fmt, "label", "list"), "test"),
        CliApiCheck(
            "gh label create",
            "gh",
            ("gh", *fmt, "label", "create", "integration", "--yes"),
            "create",
        ),
        CliApiCheck(
            "gh label delete",
            "gh",
            ("gh", *fmt, "label", "delete", "integration", "--yes"),
            "delete",
        ),
        CliApiCheck(
            "gh label sync",
            "gh",
            ("gh", *fmt, "label", "sync", "--manifest", str(manifest), "--yes"),
            "created",
        ),
        CliApiCheck("gh pr list", "gh", ("gh", *fmt, "pr", "list"), "7"),
        CliApiCheck(
            "gh pr shortcut",
            "gh",
            ("gh", *fmt, "pr", "--yes"),
            '"existing"',
        ),
        CliApiCheck("gh pr view", "gh", ("gh", *fmt, "pr", "view", "7"), "Integration PR"),
        CliApiCheck("gh pr diff", "gh", ("gh", *fmt, "pr", "diff", "7"), "file changed"),
        CliApiCheck(
            "gh pr create",
            "gh",
            ("gh", *fmt, "pr", "create", "--title", "PR", "--body", "b", "--yes"),
            "8",
        ),
        CliApiCheck(
            "gh pr edit",
            "gh",
            ("gh", *fmt, "pr", "edit", "7", "--title", "Edited PR", "--yes"),
            "edit",
        ),
        CliApiCheck(
            "gh pr comment",
            "gh",
            ("gh", *fmt, "pr", "comment", "7", "--body", "hi", "--yes"),
            "comment",
        ),
        CliApiCheck(
            "gh pr reopen",
            "gh",
            ("gh", *fmt, "pr", "reopen", "7", "--yes"),
            "open",
        ),
        CliApiCheck("gh pr checks", "gh", ("gh", *fmt, "pr", "checks", "7"), "ci"),
        CliApiCheck(
            "gh pr review",
            "gh",
            ("gh", *fmt, "pr", "review", "7", "--approve", "--body", "ok", "--yes"),
            "review",
        ),
        CliApiCheck(
            "gh pr ready",
            "gh",
            ("gh", *fmt, "pr", "ready", "7", "--yes"),
            "ready",
        ),
        CliApiCheck("gh pr status", "gh", ("gh", *fmt, "pr", "status"), "open_prs"),
        CliApiCheck(
            "gh pr close",
            "gh",
            ("gh", *fmt, "pr", "close", "7", "--yes"),
            "close",
        ),
        CliApiCheck(
            "gh pr merge",
            "gh",
            ("gh", *fmt, "pr", "merge", "7", "--yes"),
            "merge blocked",
            accept_exit_codes=(1,),
        ),
        CliApiCheck("gh backlog tree", "gh", ("gh", *fmt, "backlog", "tree"), "parents"),
        CliApiCheck("gh backlog next", "gh", ("gh", *fmt, "backlog", "next"), '"number":'),
        CliApiCheck("gh backlog levels", "gh", ("gh", *fmt, "backlog", "levels"), "levels"),
        CliApiCheck("gh backlog organize", "gh", ("gh", *fmt, "backlog", "organize"), "priority"),
        CliApiCheck(
            "gh backlog resequence",
            "gh",
            ("gh", *fmt, "backlog", "resequence", "--file", str(plan), "--yes"),
            "Resequenced",
        ),
        CliApiCheck("gh policy list", "gh", ("gh", *fmt, "policy", "list"), "pr-merge"),
        CliApiCheck("gh project list", "gh", ("gh", *fmt, "project", "list"), "Roadmap"),
        CliApiCheck("gh project view", "gh", ("gh", *fmt, "project", "view", "1"), "Roadmap"),
        CliApiCheck(
            "gh project create",
            "gh",
            ("gh", *fmt, "project", "create", "--title", "Roadmap", "--yes"),
            "Roadmap",
        ),
        CliApiCheck(
            "gh project edit",
            "gh",
            ("gh", *fmt, "project", "edit", "1", "--title", "Roadmap v2", "--yes"),
            "Roadmap",
        ),
        CliApiCheck(
            "gh project delete",
            "gh",
            ("gh", *fmt, "project", "delete", "1", "--yes"),
            "deleted",
        ),
        CliApiCheck(
            "gh project item list",
            "gh",
            ("gh", *fmt, "project", "item", "list", "1"),
            "ITEM",
        ),
        CliApiCheck(
            "gh project item view",
            "gh",
            ("gh", *fmt, "project", "item", "view", "--id", "ITEM_1", "--project", "1"),
            "ITEM",
        ),
        CliApiCheck(
            "gh project item add",
            "gh",
            ("gh", *fmt, "project", "item", "add", "--project", "1", "--issue", "42", "--yes"),
            "ITEM",
        ),
        CliApiCheck(
            "gh project item edit",
            "gh",
            (
                "gh",
                *fmt,
                "project",
                "item",
                "edit",
                "--project",
                "1",
                "--id",
                "ITEM_1",
                "--field",
                "Status",
                "--value",
                "Done",
                "--kind",
                "single-select",
                "--yes",
            ),
            "Done",
        ),
        CliApiCheck(
            "gh project item delete",
            "gh",
            ("gh", *fmt, "project", "item", "delete", "--project", "1", "--id", "ITEM_1", "--yes"),
            "deleted",
        ),
        *[
            CliApiCheck(
                f"gh ruleset {sub}",
                "gh",
                ("gh", *fmt, "ruleset", sub),
                "Rulesets blocked",
                accept_exit_codes=(1,),
            )
            for sub in ("list", "view", "create", "edit", "delete")
        ],
        CliApiCheck(
            "gh repo view",
            "gh",
            ("gh", *fmt, "repo", "view"),
            "example/repo",
        ),
        CliApiCheck("gh repo list", "gh", ("gh", *fmt, "repo", "list"), "example"),
        CliApiCheck(
            "gh repo readme-sync",
            "gh",
            ("gh", "repo", "readme-sync", "--readme", str(workspace / "README.md"), "--dry-run"),
            "README",
        ),
    ]


def _gh_failure_checks(workspace: Path) -> list[CliApiCheck]:
    failures: list[CliApiCheck] = []
    for ok in _gh_success_checks(workspace):
        if ok.accept_exit_codes != (0,):
            failures.append(
                CliApiCheck(
                    f"{ok.label} fail",
                    ok.api,
                    _without_yes(ok.args) if "--yes" in ok.args else ok.args,
                    kind="fail",
                    needle=ok.needle,
                    accept_exit_codes=ok.accept_exit_codes,
                    failure="policy_block",
                )
            )
            continue
        if "--yes" in ok.args:
            failures.append(
                CliApiCheck(
                    label=f"{ok.label} refuse",
                    api="gh",
                    args=_without_yes(ok.args),
                    kind="fail",
                    needle=REFUSE_NEEDLE,
                    accept_exit_codes=(1,),
                    failure="refuse_gate",
                )
            )
        else:
            failures.append(
                CliApiCheck(
                    label=f"{ok.label} fail",
                    api="gh",
                    args=ok.args,
                    kind="fail",
                    accept_exit_codes=(1,),
                    failure="gh_auth",
                    needle="gh",
                )
            )
    return failures


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
            "chrome photos deferred",
            "chrome",
            ("chrome", "photos"),
            kind="fail",
            needle="deferred",
            accept_exit_codes=(2,),
            failure="chrome_photos_deferred",
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


def cli_api_success_checks(*, gh_workspace: Path, drive_repo: str) -> list[CliApiCheck]:
    return [
        *_gh_success_checks(gh_workspace),
        *_notion_success_checks(),
        *_drive_success_checks(drive_repo),
        *_chrome_success_checks(),
    ]


def cli_api_failure_checks(*, gh_workspace: Path, drive_repo: str) -> list[CliApiCheck]:
    return [
        *_gh_failure_checks(gh_workspace),
        *_notion_failure_checks(),
        *_drive_failure_checks(drive_repo),
        *_chrome_failure_checks(),
    ]


def cli_api_checks(*, gh_workspace: Path, drive_repo: str) -> list[CliApiCheck]:
    return [
        *cli_api_success_checks(gh_workspace=gh_workspace, drive_repo=drive_repo),
        *cli_api_failure_checks(gh_workspace=gh_workspace, drive_repo=drive_repo),
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
    apis: tuple[ApiName, ...] = ("gh", "notion", "drive", "chrome"),
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
    apis: tuple[ApiName, ...] = ("gh", "notion", "drive", "chrome"),
) -> None:
    """Each API command path needs one success and one failure integration check."""
    local_ok_only: dict[ApiName, set[tuple[str, ...]]] = {
        "gh": {
            ("gh", "backlog", "levels"),
            ("gh", "policy", "list"),
        },
    }
    local_fail_only: dict[ApiName, set[tuple[str, ...]]] = {
        "chrome": {
            ("chrome", "photos"),
        },
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
